"""Runner for the OpenFOAM C05 transient cylinder vortex-shedding capability."""

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


def _replace_assignment(text: str, keyword: str, value: str, count: int = 1) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=count)


def _replace_vector_internal_field(text: str, vector: list[float]) -> str:
    vector_text = f"({vector[0]:g} {vector[1]:g} {vector[2]:g})"
    return re.sub(r"(internalField\s+uniform\s*)\([^)]*\)(\s*;)", lambda match: match.group(1) + vector_text + match.group(2), text, count=1)


def _replace_functions_block(text: str, replacement: str) -> str:
    return re.sub(r"\nfunctions\s*\{.*?\n\}\s*\n\n// \*+", "\n" + replacement + "\n\n// " + "*" * 73, text, count=1, flags=re.DOTALL)


def _force_coefficients_block(config: dict[str, Any]) -> str:
    force = config["function_objects"]["force_coefficients"]
    patches = " ".join(force["patches"])
    lift = force["lift_dir"]
    drag = force["drag_dir"]
    diameter = float(config["geometry"]["cylinder_diameter_m"])
    thickness = float(config["geometry"]["two_dimensional_thickness_m"])
    area = diameter * thickness
    center = config["geometry"]["cylinder_center_m"]
    mag_u = float(config["material"]["inlet_velocity_m_s"])
    rho = float(force["rho_inf_kg_m3"])
    return (
        "functions\n"
        "{\n"
        "    forceCoeffs1\n"
        "    {\n"
        "        type            forceCoeffs;\n"
        "        libs            (forces);\n"
        f"        patches         ({patches});\n"
        "        rho             rhoInf;\n"
        f"        rhoInf          {rho:g};\n"
        f"        liftDir         ({lift[0]:g} {lift[1]:g} {lift[2]:g});\n"
        f"        dragDir         ({drag[0]:g} {drag[1]:g} {drag[2]:g});\n"
        "        pitchAxis       (0 0 1);\n"
        f"        CofR            ({center[0]:g} {center[1]:g} 0);\n"
        f"        magUInf         {mag_u:g};\n"
        f"        lRef            {diameter:g};\n"
        f"        Aref            {area:g};\n"
        "        writeControl    timeStep;\n"
        "        writeInterval   1;\n"
        "    }\n"
        "}"
    )


def _restore_zero_dir(case_dir: Path) -> None:
    source = case_dir / "0.orig"
    target = case_dir / "0"
    if not source.exists():
        raise FileNotFoundError(f"OpenFOAM C05 template is missing 0.orig: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _patch_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    _restore_zero_dir(case_dir)

    control = case_dir / "system" / "controlDict"
    control_text = control.read_text(encoding="utf-8")
    control = config["numerics"]["control"]
    control_text = _replace_assignment(control_text, "endTime", f"{control['end_time_s']:g}")
    control_text = _replace_assignment(control_text, "deltaT", f"{control['delta_t_s']:g}")
    control_text = _replace_assignment(control_text, "writeInterval", f"{control['write_interval_s']:g}")
    control_text = _replace_functions_block(control_text, _force_coefficients_block(config))
    (case_dir / "system" / "controlDict").write_text(control_text, encoding="utf-8")

    transport = case_dir / "constant" / "transportProperties"
    transport_text = _replace_assignment(transport.read_text(encoding="utf-8"), "nu", f"{config['material']['kinematic_viscosity_m2_s']:g}")
    transport.write_text(transport_text, encoding="utf-8")

    u_path = case_dir / "0" / "U"
    u_text = _replace_vector_internal_field(u_path.read_text(encoding="utf-8"), config["fields"]["initial_velocity_m_s"])
    u_path.write_text(u_text, encoding="utf-8")

    fv_solution = case_dir / "system" / "fvSolution"
    solution_text = fv_solution.read_text(encoding="utf-8")
    pimple = config["numerics"]["pimple"]
    solution_text = _replace_assignment(solution_text, "nCorrectors", str(pimple["n_correctors"]))
    solution_text = _replace_assignment(solution_text, "nNonOrthogonalCorrectors", str(pimple["n_non_orthogonal_correctors"]))
    if "nOuterCorrectors" in solution_text:
        solution_text = _replace_assignment(solution_text, "nOuterCorrectors", str(pimple["n_outer_correctors"]))
    fv_solution.write_text(solution_text, encoding="utf-8")


def _generated_files(output_dir: Path) -> list[str]:
    return [path.relative_to(output_dir).as_posix() for path in sorted((output_dir / "case").rglob("*")) if path.is_file()]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
        "output_dir": str(output_dir),
        "runtime_profile": config["openfoam"]["runtime_profile"],
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "fields": config["fields"],
        "numerics": config["numerics"],
        "function_objects": config["function_objects"],
        "generated_files": generated_files,
        "mesh_commands": config["mesh"]["workflow"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": ["python:write_force_metrics"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": "dry-run manifest and generated cylinder2D template case files; no OpenFOAM solver execution",
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
    copy_template_case(runtime_identity["wsl_distro"], config["template"]["source_path"], resolved_output_dir, runtime_identity["timeout_s"])
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
        raise ValueError("OpenFOAM C05 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C05 backend {backend_type!r} is not implemented.")

    manifest["scope"] = "local WSL OpenFOAM runtime for cylinder2D pimpleFoam template case"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    runtime_outputs = write_runtime_outputs(config, resolved_output_dir, runtime)
    manifest["runtime"] = {
        "backend": runtime["backend"],
        "wsl_distro": runtime["wsl_distro"],
        "bashrc_path": runtime["bashrc_path"],
        "profile_env": runtime["profile_env"],
        "commands": runtime["commands"],
        "metrics_json": str(runtime_outputs["metrics_path"]),
        "validation_json": str(runtime_outputs["validation_path"]),
    }
    manifest["validation"] = runtime_outputs["validation"]
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
