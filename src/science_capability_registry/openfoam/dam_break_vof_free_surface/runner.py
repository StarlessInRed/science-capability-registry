"""Runner for the OpenFOAM C06 dam-break VOF capability."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import copy_template_case, resolve_runtime_identity

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import build_runtime_metrics, execute_wsl_runtime, validate_runtime_metrics, write_runtime_report
from .validation import validate_manifest


def _replace_assignment(text: str, keyword: str, value: str) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=1)


def _scale_block_counts(text: str, scale: float) -> str:
    if abs(scale - 1.0) < 1e-12:
        return text
    section = re.search(r"(blocks\s*\(\s*)(.*?)(\s*\);\s*\n\s*edges)", text, re.DOTALL)
    if section is None:
        raise ValueError("Could not locate blocks section in blockMeshDict")
    body = section.group(2)

    def repl(match: re.Match[str]) -> str:
        nx = max(1, int(round(int(match.group(1)) * scale)))
        ny = max(1, int(round(int(match.group(2)) * scale)))
        return f"({nx} {ny} 1)"

    body = re.sub(r"\((\d+)\s+(\d+)\s+1\)", repl, body)
    return text[: section.start(2)] + body + text[section.end(2) :]


def _restore_zero_dir(case_dir: Path) -> None:
    target = case_dir / "0"
    source = case_dir / "0.orig"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


def _patch_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    _restore_zero_dir(case_dir)

    control = case_dir / "system" / "controlDict"
    text = control.read_text(encoding="utf-8")
    text = _replace_assignment(text, "endTime", f"{config['numerics']['control']['end_time_s']:g}")
    text = _replace_assignment(text, "deltaT", f"{config['numerics']['control']['delta_t_s']:g}")
    text = _replace_assignment(text, "writeInterval", f"{config['numerics']['control']['write_interval_s']:g}")
    text = _replace_assignment(text, "maxCo", f"{config['numerics']['control']['max_co']:g}")
    text = _replace_assignment(text, "maxAlphaCo", f"{config['numerics']['control']['max_alpha_co']:g}")
    sampling = config["validation"]["sampling_parity"]
    if not sampling["native_sampling_enabled"]:
        text = re.sub(r"(?m)^\s*#sinclude\s+\"sampling\"\s*$\n?", "", text)
    control.write_text(text, encoding="utf-8")

    block_mesh = case_dir / "system" / "blockMeshDict"
    block_text = _scale_block_counts(block_mesh.read_text(encoding="utf-8"), float(config["mesh"]["cell_count_scale"]))
    block_mesh.write_text(block_text, encoding="utf-8")

    g_path = case_dir / "constant" / "g"
    g_text = g_path.read_text(encoding="utf-8")
    g_text = re.sub(r"value\s+\([^)]*\)\s*;", f"value           (0 -{float(config['physics']['gravity_m_s2']):g} 0);", g_text, count=1)
    g_path.write_text(g_text, encoding="utf-8")

    set_fields = case_dir / "system" / "setFieldsDict"
    set_text = set_fields.read_text(encoding="utf-8")
    height = float(config["initial_conditions"]["water_column_height_m"])
    width = float(config["initial_conditions"]["water_column_width_m"])
    set_text = re.sub(r"box\s+\(0\s+0\s+-1\)\s+\([^)]*\)\s*;", f"box (0 0 -1) ({width:g} {height:g} 1);", set_text, count=1)
    set_fields.write_text(set_text, encoding="utf-8")


def _generated_files(output_dir: Path) -> list[str]:
    return [path.relative_to(output_dir).as_posix() for path in sorted((output_dir / "case").rglob("*")) if path.is_file()]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C06_dam_break_vof_free_surface.schema.json",
        "output_dir": str(output_dir),
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "generated_files": generated_files,
        "mesh_commands": ["blockMesh"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": ["python:write_vof_metrics"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": "dry-run manifest and generated case files; no OpenFOAM solver execution",
    }


def run(config_path: str | Path | None = None, config: dict[str, Any] | None = None, output_dir: str | Path | None = None, dry_run: bool = False, backend: str | None = None) -> dict[str, Any]:
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
        raise ValueError("OpenFOAM C06 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C06 backend {backend_type!r} is not implemented.")
    manifest["scope"] = "local WSL OpenFOAM runtime for dam-break interFoam template case"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    metrics = build_runtime_metrics(config, resolved_output_dir, runtime)
    metrics_path = resolved_output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_runtime_metrics(metrics, config, resolved_output_dir)
    validation_path = resolved_output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_runtime_report(config, metrics, validation, resolved_output_dir)
    manifest["runtime"] = {"backend": runtime["backend"], "wsl_distro": runtime["wsl_distro"], "bashrc_path": runtime["bashrc_path"], "profile_env": runtime["profile_env"], "commands": runtime["commands"], "metrics_json": str(metrics_path), "validation_json": str(validation_path)}
    manifest["validation"] = validation
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
