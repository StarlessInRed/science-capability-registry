"""Runner for the OpenFOAM C07 conjugate heat-transfer cooling capability."""

from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import (
    copy_template_case,
    map_windows_path_to_wsl,
    resolve_runtime_identity,
    run_wsl,
)

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import build_runtime_metrics, execute_wsl_runtime, validate_runtime_metrics, write_runtime_report
from .validation import validate_manifest


def _replace_assignment(text: str, keyword: str, value: str, count: int = 1) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=count)


def _replace_internal_temperature(text: str, value: float) -> str:
    return re.sub(r"(internalField\s+uniform\s+)[^;]+;", rf"\g<1>{value:g};", text, count=1)


def _format_vector(vector: list[float]) -> str:
    if len(vector) != 3:
        raise ValueError(f"Expected a 3-component OpenFOAM vector, got {vector!r}.")
    return f"({float(vector[0]):g} {float(vector[1]):g} {float(vector[2]):g})"


def _replace_field_internal_vector(text: str, field_name: str, vector: list[float]) -> str:
    pattern = rf"(\b{re.escape(field_name)}\s*\{{.*?\binternalField\s+uniform\s+)\([^;]+\);"
    updated, count = re.subn(pattern, rf"\g<1>{_format_vector(vector)};", text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Could not patch {field_name!r} internal vector field.")
    return updated


def _replace_field_patch_vector(text: str, field_name: str, patch_name: str, keyword: str, vector: list[float]) -> str:
    pattern = (
        rf"(\b{re.escape(field_name)}\s*\{{.*?\bboundaryField\s*\{{.*?"
        rf"\b{re.escape(patch_name)}\s*\{{.*?\b{re.escape(keyword)}\s+uniform\s+)\([^;]+\);"
    )
    updated, count = re.subn(pattern, rf"\g<1>{_format_vector(vector)};", text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Could not patch {field_name!r}.{patch_name!r}.{keyword!r} vector.")
    return updated


def _replace_heat_source_power(text: str, power_w: float) -> str:
    return re.sub(r"(h\s*)\(\s*[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?\s+0\s*\)(\s*;)", rf"\g<1>( {power_w:g} 0 )\2", text, count=1)


def _replace_fixed_boundary_temperature(text: str, patch_name: str, temperature_k: float) -> str:
    pattern = rf"({re.escape(patch_name)}\s*\{{[^{{}}]*?type\s+fixedValue;\s*value\s+uniform\s+)[^;]+;"
    replacement = rf"\g<1>{temperature_k:g};"
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"Could not patch fixed-temperature boundary {patch_name!r}.")
    return updated


def _remove_probe_function_object(text: str) -> str:
    return re.sub(r"\nfunctions\s*\{.*?#include\s+\"probes\".*?\}\s*", "\n", text, flags=re.DOTALL)


def _empty_dictionary_block(text: str, keyword: str) -> str:
    match = re.search(rf"\b{re.escape(keyword)}\s*\{{", text)
    if match is None:
        return text
    brace_start = text.find("{", match.start())
    depth = 0
    for index in range(brace_start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[: match.start()] + f"{keyword}\n{{\n}}\n" + text[index + 1 :]
    raise ValueError(f"Could not find closing brace for OpenFOAM dictionary block {keyword!r}.")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _copy_geometry_resource(config: dict[str, Any], output_dir: Path, distro: str, timeout_s: float) -> None:
    if "geometry_resource_path" not in config["template"]:
        return
    case_dir_linux = map_windows_path_to_wsl(output_dir / "case", distro, timeout_s)
    source = config["template"]["geometry_resource_path"]
    target = f"{case_dir_linux}/constant/triSurface"
    script = (
        f"test -d {shlex.quote(source)} || exit 2; "
        f"mkdir -p {shlex.quote(target)}; "
        f"cp -a {shlex.quote(source)}/. {shlex.quote(target)}/"
    )
    result = run_wsl(distro, script, timeout_s)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to copy OpenFOAM C07 geometry resource: {detail}")


def _materialize_initial_fields(case_dir: Path) -> None:
    source = case_dir / "0.orig"
    target = case_dir / "0"
    if not source.exists():
        raise FileNotFoundError(f"OpenFOAM C07 template is missing 0.orig: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _patch_control_dict(case_dir: Path, config: dict[str, Any]) -> None:
    path = case_dir / "system" / "controlDict"
    text = path.read_text(encoding="utf-8")
    control = config["numerics"]["control"]
    text = _remove_probe_function_object(text)
    if config["template"].get("disabled_function_objects"):
        text = _empty_dictionary_block(text, "functions")
    text = _replace_assignment(text, "endTime", f"{control['end_time_iterations']:g}")
    text = _replace_assignment(text, "deltaT", f"{control['delta_t']:g}")
    text = _replace_assignment(text, "writeInterval", f"{control['write_interval']:g}")
    text = _replace_assignment(text, "writeFormat", str(control["write_format"]))
    _write_text(path, text)


def _patch_decompose_dicts(case_dir: Path, config: dict[str, Any]) -> None:
    root_path = case_dir / "system" / "decomposeParDict"
    root_text = root_path.read_text(encoding="utf-8")
    root_text = _replace_assignment(root_text, "numberOfSubdomains", str(config["parallel"]["number_of_subdomains"]), count=1)
    root_text = _replace_assignment(root_text, "method", config["parallel"]["method"], count=1)
    _write_text(root_path, root_text)

    for region, subdomains in config["parallel"]["region_subdomains"].items():
        path = case_dir / "system" / region / "decomposeParDict"
        try:
            if not path.exists() or path.is_symlink():
                continue
        except OSError:
            continue
        text = path.read_text(encoding="utf-8")
        text = _replace_assignment(text, "numberOfSubdomains", str(subdomains), count=0)
        _write_text(path, text)


def _patch_block_mesh_cells(case_dir: Path, config: dict[str, Any]) -> None:
    cells = config["mesh_workflow"].get("block_mesh_cells")
    if cells is None:
        return
    path = case_dir / "system" / "blockMeshDict"
    text = path.read_text(encoding="utf-8")
    cell_text = f"({int(cells[0])} {int(cells[1])} {int(cells[2])})"
    updated, count = re.subn(r"(hex\s*\([^)]*\)\s*)\(\s*\d+\s+\d+\s+\d+\s*\)", rf"\g<1>{cell_text}", text, count=1)
    if count != 1:
        raise ValueError("Could not patch blockMeshDict hex cell counts.")
    _write_text(path, updated)


def _patch_temperature_fields(case_dir: Path, config: dict[str, Any]) -> None:
    initial_temperature = float(config["fields"]["initial_temperature_K"])
    for region in [*config["regions"]["fluid"], *config["regions"]["solid"]]:
        path = case_dir / "0" / region / "T"
        text = _replace_internal_temperature(path.read_text(encoding="utf-8"), initial_temperature)
        _write_text(path, text)


def _patch_heat_source(case_dir: Path, config: dict[str, Any]) -> None:
    power_w = float(config["heat_sources"]["v_CPU"]["power_W"])
    path = case_dir / "system" / "v_CPU" / "fvOptions"
    text = _replace_heat_source_power(path.read_text(encoding="utf-8"), power_w)
    _write_text(path, text)


def _patch_fixed_temperature_sources(case_dir: Path, config: dict[str, Any]) -> None:
    for region, source in config["heat_sources"].items():
        if source["source_type"] != "fixed_temperature_boundary":
            continue
        path = case_dir / "system" / region / "changeDictionaryDict"
        text = path.read_text(encoding="utf-8")
        text = _replace_fixed_boundary_temperature(text, str(source["boundary_patch"]), float(source["temperature_K"]))
        _write_text(path, text)


def _patch_velocity_overrides(case_dir: Path, config: dict[str, Any]) -> None:
    overrides = config["fields"].get("velocity_overrides_m_s", {})
    for region, settings in overrides.items():
        path = case_dir / "system" / region / "changeDictionaryDict"
        text = path.read_text(encoding="utf-8")
        if "internal" in settings:
            text = _replace_field_internal_vector(text, "U", settings["internal"])
        for patch_name, patch_settings in settings.get("boundary_values", {}).items():
            for keyword, vector in patch_settings.items():
                text = _replace_field_patch_vector(text, "U", patch_name, keyword, vector)
        _write_text(path, text)


def _patch_mrf(case_dir: Path, config: dict[str, Any]) -> None:
    if "mrf" not in config["numerics"]:
        return
    path = case_dir / "constant" / "domain0" / "MRFProperties"
    text = path.read_text(encoding="utf-8")
    text = _replace_assignment(text, "omega", f"{config['numerics']['mrf']['omega_rad_s']:g}")
    _write_text(path, text)


def _patch_fluid_material(case_dir: Path, config: dict[str, Any]) -> None:
    for region in config["regions"]["fluid"]:
        material = config["materials"][region]
        path = case_dir / "constant" / region / "thermophysicalProperties"
        text = path.read_text(encoding="utf-8")
        text = _replace_assignment(text, "molWeight", f"{material['mol_weight']:g}")
        text = _replace_assignment(text, "Cp", f"{material['cp_J_kg_K']:g}")
        text = _replace_assignment(text, "mu", f"{material['dynamic_viscosity_Pa_s']:g}")
        text = _replace_assignment(text, "Pr", f"{material['prandtl']:g}")
        _write_text(path, text)


def _patch_solid_materials(case_dir: Path, config: dict[str, Any]) -> None:
    for region in config["regions"]["solid"]:
        material = config["materials"][region]
        path = case_dir / "constant" / region / "thermophysicalProperties"
        text = path.read_text(encoding="utf-8")
        text = _replace_assignment(text, "Cp", f"{material['cp_J_kg_K']:g}")
        text = _replace_assignment(text, "kappa", f"{material['thermal_conductivity_W_m_K']:g}")
        text = _replace_assignment(text, "rho", f"{material['density_kg_m3']:g}")
        _write_text(path, text)


def _patch_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    _patch_control_dict(case_dir, config)
    _patch_decompose_dicts(case_dir, config)
    _patch_block_mesh_cells(case_dir, config)
    _patch_velocity_overrides(case_dir, config)
    _patch_fluid_material(case_dir, config)
    _patch_solid_materials(case_dir, config)
    source_profile_key = config["template"]["source_profile_key"]
    if source_profile_key == "c07_cpu_cabinet":
        _materialize_initial_fields(case_dir)
        _patch_temperature_fields(case_dir, config)
        _patch_heat_source(case_dir, config)
        _patch_mrf(case_dir, config)
    elif source_profile_key == "c07_multi_region_heater_radiation":
        _patch_fixed_temperature_sources(case_dir, config)
    else:
        raise ValueError(f"Unsupported C07 template source_profile_key: {source_profile_key!r}")


def _generated_files(output_dir: Path) -> list[str]:
    generated = []
    for path in sorted((output_dir / "case").rglob("*")):
        try:
            is_file = path.is_file()
        except OSError:
            continue
        if is_file:
            generated.append(path.relative_to(output_dir).as_posix())
    return generated


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C07_conjugate_heat_transfer_cooling.schema.json",
        "output_dir": str(output_dir),
        "runtime_profile": config["openfoam"]["runtime_profile"],
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "regions": config["regions"],
        "interfaces": [item["name"] for item in config["interfaces"]],
        "generated_files": generated_files,
        "mesh_commands": config["mesh_workflow"]["command_sequence"],
        "radiation_commands": config["radiation"]["preprocessing_commands"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": config["postprocess"]["command_sequence"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": f"dry-run manifest and generated {config['template']['source_profile_key']} multi-region CHT case files; no OpenFOAM solver execution",
    }


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
    backend: str | None = None,
) -> dict[str, Any]:
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)
    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_case_config(config)

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    runtime_identity = resolve_runtime_identity(config)
    timeout_s = runtime_identity["timeout_s"]
    distro = runtime_identity["wsl_distro"]
    copy_template_case(distro, config["template"]["source_path"], resolved_output_dir, timeout_s)
    _copy_geometry_resource(config, resolved_output_dir, distro, timeout_s)
    _patch_case_files(resolved_output_dir, config)
    generated_files = _generated_files(resolved_output_dir)
    manifest = _build_manifest(config, resolved_output_dir, generated_files)

    if dry_run:
        validation = validate_manifest(manifest, config, resolved_output_dir)
        manifest["validation"] = validation
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("OpenFOAM C07 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C07 backend {backend_type!r} is not implemented.")

    manifest["scope"] = f"local WSL OpenFOAM runtime smoke for {config['template']['source_profile_key']} multi-region CHT template case"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    metrics = build_runtime_metrics(config, resolved_output_dir, runtime)
    metrics_path = resolved_output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_runtime_metrics(metrics, config, resolved_output_dir)
    validation_path = resolved_output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_runtime_report(config, metrics, validation, resolved_output_dir)
    manifest["runtime"] = {
        "backend": runtime["backend"],
        "wsl_distro": runtime["wsl_distro"],
        "bashrc_path": runtime["bashrc_path"],
        "profile_env": runtime["profile_env"],
        "commands": runtime["commands"],
        "metrics_json": str(metrics_path),
        "validation_json": str(validation_path),
    }
    manifest["validation"] = validation
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
