"""Runner for the OpenFOAM C02 potential-flow cylinder capability."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import copy_template_case, resolve_runtime_identity

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import execute_wsl_runtime, write_runtime_outputs
from .validation import validate_manifest


def _replace_assignment(text: str, keyword: str, value: str) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=1)


def _replace_uniform_value_vector(text: str, patch: str, vector: list[float]) -> str:
    vector_text = f"({vector[0]:g} {vector[1]:g} {vector[2]:g})"
    pattern = rf"({re.escape(patch)}\s*\{{.*?uniformValue\s+constant\s*)\([^)]*\)(\s*;)"
    return re.sub(pattern, lambda match: match.group(1) + vector_text + match.group(2), text, count=1, flags=re.DOTALL)


def _replace_fixed_value_scalar(text: str, patch: str, value: float) -> str:
    pattern = rf"({re.escape(patch)}\s*\{{.*?value\s+uniform\s*)[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(\s*;)"
    return re.sub(pattern, lambda match: match.group(1) + f"{value:g}" + match.group(2), text, count=1, flags=re.DOTALL)


def _remove_function_objects(text: str) -> str:
    return re.sub(r"\nfunctions\s*\{.*?\n\}\s*\n\s*// \*{9,}.*", "\n\n// ************************************************************************* //\n", text, count=1, flags=re.DOTALL)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _prepare_zero_dir(case_dir: Path, zero_source_dir: str) -> None:
    target = case_dir / "0"
    source = case_dir / zero_source_dir
    if target.exists():
        return
    if not source.exists():
        raise FileNotFoundError(f"OpenFOAM zero source directory not found: {source}")
    shutil.copytree(source, target)


def _patch_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    _prepare_zero_dir(case_dir, config["template"]["zero_source_dir"])

    control = case_dir / "system" / "controlDict"
    control_text = control.read_text(encoding="utf-8")
    control_text = _remove_function_objects(control_text)
    control_text = _replace_assignment(control_text, "endTime", f"{config['numerics']['control']['end_time']:g}")
    control_text = _replace_assignment(control_text, "writeInterval", f"{config['numerics']['control']['write_interval']:g}")
    _write_text(control, control_text)

    fv_solution = case_dir / "system" / "fvSolution"
    fv_solution_text = fv_solution.read_text(encoding="utf-8")
    fv_solution_text = _replace_assignment(fv_solution_text, "nNonOrthogonalCorrectors", str(config["numerics"]["potential_flow"]["n_non_orthogonal_correctors"]))
    fv_solution_text = _replace_assignment(fv_solution_text, "tolerance", f"{config['numerics']['potential_flow']['phi_tolerance']:g}")
    _write_text(fv_solution, fv_solution_text)

    block_mesh = case_dir / "system" / "blockMeshDict"
    block_text = block_mesh.read_text(encoding="utf-8")
    geometry = config["geometry"]
    mesh = config["mesh"]
    replacements = {
        "rInner": f"{geometry['cylinder_radius_m']:g}",
        "rOuter": f"{geometry['outer_radius_m']:g}",
        "xmax": f"{geometry['domain_half_width_m']:g}",
        "ymax": f"{geometry['domain_half_width_m']:g}",
        "zmin": f"{-float(geometry['two_dimensional_thickness_m']) / 2.0:g}",
        "zmax": f"{float(geometry['two_dimensional_thickness_m']) / 2.0:g}",
        "nRadial": str(mesh["n_radial"]),
        "nQuarter": str(mesh["n_quarter"]),
        "nxOuter": str(mesh["n_outer_x"]),
        "nyOuter": str(mesh["n_outer_y"]),
        "nz": str(mesh["n_z"]),
    }
    for key, value in replacements.items():
        block_text = _replace_assignment(block_text, key, value)
    _write_text(block_mesh, block_text)

    u_path = case_dir / "0" / "U"
    u_text = _replace_uniform_value_vector(
        u_path.read_text(encoding="utf-8"),
        "left",
        [float(config["material"]["inlet_velocity_m_s"]), 0.0, 0.0],
    )
    _write_text(u_path, u_text)

    p_path = case_dir / "0" / "p"
    p_text = _replace_fixed_value_scalar(
        p_path.read_text(encoding="utf-8"),
        "right",
        float(config["material"]["p_reference_kinematic_m2_s2"]),
    )
    _write_text(p_path, p_text)


def _generated_files(output_dir: Path) -> list[str]:
    return [path.relative_to(output_dir).as_posix() for path in sorted((output_dir / "case").rglob("*")) if path.is_file()]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C02_potential_flow_cylinder_analytical_validation.schema.json",
        "output_dir": str(output_dir),
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "fields": config["fields"],
        "numerics": config["numerics"],
        "analytical_reference": config["analytical_reference"],
        "function_objects": config["function_objects"],
        "generated_files": generated_files,
        "mesh_commands": ["blockMesh"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": ["python:write_analytical_metrics"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": "dry-run manifest and generated case files; no OpenFOAM solver execution",
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
        raise ValueError("OpenFOAM C02 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C02 backend {backend_type!r} is not implemented.")

    manifest["scope"] = "local WSL OpenFOAM runtime for potential-flow cylinder template case"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    outputs = write_runtime_outputs(config, resolved_output_dir, runtime)
    manifest["runtime"] = {
        "backend": runtime["backend"],
        "wsl_distro": runtime["wsl_distro"],
        "bashrc_path": runtime["bashrc_path"],
        "profile_env": runtime["profile_env"],
        "commands": runtime["commands"],
        "metrics_json": str(outputs["metrics_path"]),
        "validation_json": str(outputs["validation_path"]),
    }
    manifest["validation"] = outputs["validation"]
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
