"""Validation for OpenFOAM C04 dry-run and runtime artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _contains_in_order(items: list[str], expected: list[str]) -> bool:
    cursor = 0
    for item in items:
        if cursor < len(expected) and expected[cursor] in item:
            cursor += 1
    return cursor == len(expected)


def validate_manifest(
    manifest: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    generated_files = set(manifest.get("generated_files", []))
    backend = manifest.get("backend", {})
    solver = manifest.get("solver", {})
    mesh_commands = manifest.get("mesh_commands", [])
    solver_commands = manifest.get("solver_commands", [])
    function_objects = config["function_objects"]
    geometry = config["geometry"]
    mesh_quality = config["mesh"]["quality"]
    turbulence = config["turbulence"]

    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(checks, "solver.simpleFoam", solver.get("name") == "simpleFoam", json.dumps(solver, ensure_ascii=False))
    _check(checks, "template.official_motorBike", "simpleFoam/motorBike" in config["template"]["source_path"], config["template"]["source_path"])
    _check(
        checks,
        "mesh.workflow_order",
        _contains_in_order([*mesh_commands, *solver_commands], ["surfaceFeatureExtract", "blockMesh", "decomposePar", "snappyHexMesh", "topoSet", "checkMesh", "simpleFoam"]),
        json.dumps([*mesh_commands, *solver_commands], ensure_ascii=False),
    )
    _check(checks, "solver_commands.snappyHexMesh", any("snappyHexMesh" in command for command in solver_commands), json.dumps(solver_commands, ensure_ascii=False))
    _check(checks, "solver_commands.checkMesh", any("checkMesh" in command for command in solver_commands), json.dumps(solver_commands, ensure_ascii=False))
    _check(checks, "solver_commands.simpleFoam", any("simpleFoam" in command for command in solver_commands), json.dumps(solver_commands, ensure_ascii=False))
    _check(checks, "mesh.quality_thresholds", all(float(mesh_quality[key]) > 0 for key in ["max_non_orthogonality", "max_skewness", "max_aspect_ratio"]) and int(mesh_quality["min_cell_count"]) > 0, json.dumps(mesh_quality, ensure_ascii=False))
    force = function_objects["force_coefficients"]
    if force["enabled"] is True:
        _check(checks, "forceCoeffs.enabled", True, json.dumps(force, ensure_ascii=False))
        _check(checks, "forceCoeffs.patch_declared", "motorBikeGroup" in force["patches"], json.dumps(force, ensure_ascii=False))
        _check(checks, "forceCoeffs.normalization", float(geometry["reference_area_m2"]) > 0.0 and float(config["material"]["density_kg_m3"]) > 0.0 and float(config["material"]["inlet_velocity_m_s"]) > 0.0, json.dumps(geometry, ensure_ascii=False))
    else:
        _check(checks, "forceCoeffs.not_required", config["postprocess"]["force_extraction_source"] == "not_required", json.dumps(force, ensure_ascii=False))
    if function_objects["y_plus"]["required"] is True:
        _check(checks, "yPlus.contract", float(turbulence["wall_function_y_plus_min"]) < float(turbulence["wall_function_y_plus_max"]), json.dumps(turbulence, ensure_ascii=False))
    else:
        _check(checks, "yPlus.not_required", "y_plus_min_max_mean" not in config["postprocess"]["required_metrics"], json.dumps(function_objects["y_plus"], ensure_ascii=False))
    _check(checks, "scope.no_runtime_claim", "no OpenFOAM solver execution" in manifest.get("scope", ""), manifest.get("scope", ""))

    for rel_path in config["validation"]["required_generated_files"]:
        _check(checks, f"generated_file.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(checks, f"generated_file.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run manifest and generated motorBike snappy template case files only",
        "checks": checks,
    }


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    commands = metrics.get("runtime", {}).get("commands", [])
    mesh = metrics.get("mesh", {})
    solver = metrics.get("solver", {})
    forces = metrics.get("postprocess", {}).get("force_coefficients", {})
    y_plus = metrics.get("postprocess", {}).get("y_plus", {})

    for command in config["solver"]["command_sequence"]:
        match = next((item for item in commands if item.get("command") == command), None)
        _check(checks, f"command.{command}.returncode", bool(match and match.get("returncode") == 0), json.dumps(match or {}, ensure_ascii=False))

    _check(checks, "mesh.snappy_completed", mesh.get("snappy_completed") is True, json.dumps(mesh, ensure_ascii=False))
    _check(checks, "mesh.checkMesh_ok", mesh.get("mesh_ok") is True, json.dumps(mesh, ensure_ascii=False))
    _check(checks, "mesh.cell_count", int(mesh.get("cell_count", 0)) >= int(config["mesh"]["quality"]["min_cell_count"]), json.dumps(mesh, ensure_ascii=False))
    _check(checks, "mesh.max_non_orthogonality", _is_finite(mesh.get("max_non_orthogonality")) and float(mesh["max_non_orthogonality"]) <= float(config["mesh"]["quality"]["max_non_orthogonality"]), json.dumps(mesh, ensure_ascii=False))
    _check(checks, "mesh.max_aspect_ratio", _is_finite(mesh.get("max_aspect_ratio")) and float(mesh["max_aspect_ratio"]) <= float(config["mesh"]["quality"]["max_aspect_ratio"]), json.dumps(mesh, ensure_ascii=False))
    _check(checks, "mesh.max_skewness", _is_finite(mesh.get("max_skewness")) and float(mesh["max_skewness"]) <= float(config["mesh"]["quality"]["max_skewness"]), json.dumps(mesh, ensure_ascii=False))

    _check(checks, "solver.started", solver.get("started") is True, json.dumps(solver, ensure_ascii=False))
    _check(checks, "solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    residual = solver.get("max_final_residual")
    _check(checks, "solver.final_residual", _is_finite(residual) and float(residual) <= float(config["validation"]["max_final_residual"]), f"value={residual}")

    if config["function_objects"]["force_coefficients"]["enabled"]:
        _check(checks, "force.available", forces.get("available") is True, json.dumps(forces, ensure_ascii=False))
        _check(checks, "force.cd_finite", _is_finite(forces.get("cd_tail_mean")), json.dumps(forces, ensure_ascii=False))
        _check(checks, "force.cl_finite", _is_finite(forces.get("cl_tail_mean")), json.dumps(forces, ensure_ascii=False))
        _check(checks, "force.cd_stability", _is_finite(forces.get("cd_tail_std")) and float(forces["cd_tail_std"]) <= float(config["validation"]["max_force_coefficient_std"]), json.dumps(forces, ensure_ascii=False))
        _check(checks, "force.cl_stability", _is_finite(forces.get("cl_tail_std")) and float(forces["cl_tail_std"]) <= float(config["validation"]["max_force_coefficient_std"]), json.dumps(forces, ensure_ascii=False))
    else:
        _check(checks, "force.not_required", forces.get("required") is False and forces.get("available") is False, json.dumps(forces, ensure_ascii=False))

    if config["function_objects"]["y_plus"]["required"]:
        _check(checks, "yPlus.available", y_plus.get("available") is True, json.dumps(y_plus, ensure_ascii=False))
        _check(checks, "yPlus.finite", _is_finite(y_plus.get("min")) and _is_finite(y_plus.get("max")) and _is_finite(y_plus.get("mean")), json.dumps(y_plus, ensure_ascii=False))
        _check(checks, "yPlus.range", _is_finite(y_plus.get("min")) and _is_finite(y_plus.get("max")) and float(y_plus["min"]) >= float(config["validation"]["min_y_plus"]) and float(y_plus["max"]) <= float(config["validation"]["max_y_plus"]), json.dumps(y_plus, ensure_ascii=False))
    else:
        _check(checks, "yPlus.not_required", y_plus.get("required") is False and y_plus.get("available") is False, json.dumps(y_plus, ensure_ascii=False))

    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        _check(checks, f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local OpenFOAM C04 runtime with mesh quality, forceCoeffs, residual, and y+ validation",
        "checks": checks,
    }
