"""Runner for the OpenFOAM C08 forward-step shock-capturing capability."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import copy_template_case, resolve_runtime_identity

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import execute_wsl_runtime, write_runtime_outputs
from .validation import validate_manifest


def _replace_assignment(text: str, keyword: str, value: str) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=1)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _prepare_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    control = case_dir / "system" / "controlDict"
    control_text = control.read_text(encoding="utf-8")
    control_cfg = config["numerics"]["control"]
    control_text = _replace_assignment(control_text, "startTime", f"{control_cfg['start_time_s']:g}")
    control_text = _replace_assignment(control_text, "endTime", f"{control_cfg['end_time_s']:g}")
    control_text = _replace_assignment(control_text, "deltaT", f"{control_cfg['delta_t_s']:g}")
    control_text = _replace_assignment(control_text, "writeInterval", f"{control_cfg['write_interval_s']:g}")
    control_text = _replace_assignment(control_text, "adjustTimeStep", "yes" if control_cfg["adjust_time_step"] else "no")
    control_text = _replace_assignment(control_text, "maxCo", f"{control_cfg['max_courant']:g}")
    control_text = _replace_assignment(control_text, "maxDeltaT", f"{control_cfg['max_delta_t_s']:g}")
    _write_text(control, control_text)


def _generated_files(output_dir: Path) -> list[str]:
    return [path.relative_to(output_dir).as_posix() for path in sorted((output_dir / "case").rglob("*")) if path.is_file()]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C08_compressible_shock_capturing_forward_step.schema.json",
        "output_dir": str(output_dir),
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "thermophysical_properties": config["thermophysical_properties"],
        "fields": config["fields"],
        "boundary_conditions": config["boundary_conditions"],
        "numerics": config["numerics"],
        "postprocess": config["postprocess"],
        "shock_reference": config["shock_reference"],
        "generated_files": generated_files,
        "mesh_commands": ["blockMesh", "checkMesh"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": [
            "python:write_shock_metrics",
            "python:compute_boundary_flux_conservation_proxy",
            "python:compute_face_field_flux_parity",
        ],
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
    _prepare_case_files(resolved_output_dir, config)
    generated_files = _generated_files(resolved_output_dir)
    manifest = _build_manifest(config, resolved_output_dir, generated_files)

    if dry_run:
        validation = validate_manifest(manifest, config, resolved_output_dir)
        manifest["validation"] = validation
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("OpenFOAM C08 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C08 backend {backend_type!r} is not implemented.")

    manifest["scope"] = "local WSL OpenFOAM runtime for rhoCentralFoam forwardStep template case"
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
