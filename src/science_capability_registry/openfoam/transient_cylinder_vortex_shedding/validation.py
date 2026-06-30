"""Validation for OpenFOAM C05 dry-run and runtime artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

OPENFOAM_FORCE_COEFFS = "openfoam_forceCoeffs"


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _uses_openfoam_force_coeffs(config: dict[str, Any]) -> bool:
    return config["postprocess"].get("force_extraction_source", OPENFOAM_FORCE_COEFFS) == OPENFOAM_FORCE_COEFFS


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    backend = manifest.get("backend", {})
    solver = manifest.get("solver", {})
    force_coeffs = manifest.get("function_objects", {}).get("force_coefficients", {})
    material = config["material"]
    geometry = config["geometry"]
    generated_files = set(manifest.get("generated_files", []))
    force_required = bool(config["validation"]["force_coefficients_required"])
    openfoam_force_coeffs_required = force_required and _uses_openfoam_force_coeffs(config)

    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(checks, "solver.pimpleFoam", solver.get("name") == "pimpleFoam", json.dumps(solver, ensure_ascii=False))
    _check(checks, "template.official_cylinder2D", "cylinder2D" in config["template"]["source_path"], config["template"]["source_path"])
    _check(checks, "physics.positive_reynolds", float(material["reynolds_number_D"]) > 0.0, str(material["reynolds_number_D"]))
    _check(checks, "physics.positive_inlet_velocity", float(material["inlet_velocity_m_s"]) > 0.0, str(material["inlet_velocity_m_s"]))
    _check(checks, "physics.positive_viscosity", float(material["kinematic_viscosity_m2_s"]) > 0.0, str(material["kinematic_viscosity_m2_s"]))
    _check(checks, "geometry.positive_diameter", float(geometry["cylinder_diameter_m"]) > 0.0, str(geometry["cylinder_diameter_m"]))
    _check(
        checks,
        "function_object.force_coefficients_enabled",
        force_coeffs.get("enabled") is True or not openfoam_force_coeffs_required,
        json.dumps(force_coeffs, ensure_ascii=False),
    )
    _check(
        checks,
        "function_object.force_coefficients_patch",
        "cylinder" in force_coeffs.get("patches", []) or not openfoam_force_coeffs_required,
        json.dumps(force_coeffs, ensure_ascii=False),
    )

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
        "scope": "dry-run manifest and generated official cylinder2D template case files only",
        "checks": checks,
    }


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    runtime_commands = metrics.get("runtime", {}).get("commands", [])
    solver = metrics.get("solver", {})
    postprocess = metrics.get("postprocess", {})

    for command in config["solver"]["command_sequence"]:
        match = next((item for item in runtime_commands if item.get("command") == command), None)
        _check(checks, f"command.{command}.returncode", bool(match and match.get("returncode") == 0), json.dumps(match or {}, ensure_ascii=False))

    final_time = solver.get("final_time")
    max_courant = solver.get("max_courant_number")
    control = config["numerics"]["control"]
    final_time_tolerance = max(
        float(control.get("delta_t_s", 0.0)),
        float(control.get("max_delta_t_s", 0.0)),
        1e-12,
    )
    _check(checks, "solver.started", solver.get("started") is True, "time or residual signal found")
    _check(checks, "solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    _check(
        checks,
        "solver.final_time",
        _is_finite(final_time) and float(final_time) >= float(control["end_time_s"]) - final_time_tolerance,
        f"final_time={final_time}, target={control['end_time_s']}, tolerance={final_time_tolerance}",
    )
    _check(checks, "solver.max_courant", _is_finite(max_courant) and float(max_courant) <= float(config["validation"]["max_courant"]), str(max_courant))

    max_final = max(
        (float(row["final"]) for row in solver.get("residual_history", []) if _is_finite(row.get("final"))),
        default=float("inf"),
    )
    _check(checks, "solver.final_residual_threshold", math.isfinite(max_final) and max_final <= float(config["validation"]["max_final_residual"]), f"max_final_residual={max_final}")

    force = postprocess.get("force_coefficients", {})
    if config["validation"]["force_coefficients_required"]:
        _check(checks, "postprocess.force_coefficients", force.get("available") is True, json.dumps(force, ensure_ascii=False))
        expected_source = config["postprocess"].get("force_extraction_source", OPENFOAM_FORCE_COEFFS)
        _check(checks, "postprocess.force_coefficients_source", force.get("source") == expected_source, json.dumps(force, ensure_ascii=False))
        if "min_force_samples" in config["validation"]:
            row_count = force.get("row_count")
            _check(
                checks,
                "postprocess.force_sample_count",
                _is_finite(row_count) and int(row_count) >= int(config["validation"]["min_force_samples"]),
                f"row_count={row_count}, minimum={config['validation']['min_force_samples']}",
            )
        if "min_force_time_span_s" in config["validation"]:
            time_span = force.get("time_span_s")
            _check(
                checks,
                "postprocess.force_time_span",
                _is_finite(time_span) and float(time_span) >= float(config["validation"]["min_force_time_span_s"]),
                f"time_span_s={time_span}, minimum={config['validation']['min_force_time_span_s']}",
            )
        nonfinite_count = force.get("nonfinite_count")
        if nonfinite_count is not None:
            _check(checks, "postprocess.force_finite_values", int(nonfinite_count) == 0, f"nonfinite_count={nonfinite_count}")
    else:
        _check(checks, "postprocess.force_coefficients_not_required", True, "force coefficient functionObject is disabled for solver-only smoke")
    if config["postprocess"]["strouhal_estimate"]:
        strouhal = postprocess.get("strouhal", {})
        _check(checks, "postprocess.strouhal_available", strouhal.get("available") is True, json.dumps(strouhal, ensure_ascii=False))
        value = strouhal.get("strouhal_number")
        lower, upper = config["validation"]["strouhal_target_range"]
        _check(
            checks,
            "postprocess.strouhal_target_range",
            _is_finite(value) and float(lower) <= float(value) <= float(upper),
            f"strouhal={value}, target=[{lower}, {upper}]",
        )
        if "min_lift_peak_count" in config["validation"]:
            peak_count = strouhal.get("peak_count")
            _check(
                checks,
                "postprocess.strouhal_peak_count",
                _is_finite(peak_count) and int(peak_count) >= int(config["validation"]["min_lift_peak_count"]),
                f"peak_count={peak_count}, minimum={config['validation']['min_lift_peak_count']}",
            )
        if "max_period_cv" in config["validation"]:
            period_cv = strouhal.get("period_cv")
            _check(
                checks,
                "postprocess.strouhal_period_cv",
                _is_finite(period_cv) and float(period_cv) <= float(config["validation"]["max_period_cv"]),
                f"period_cv={period_cv}, maximum={config['validation']['max_period_cv']}",
            )
        if "min_cl_amplitude" in config["validation"]:
            cl_amplitude = strouhal.get("cl_amplitude")
            _check(
                checks,
                "postprocess.strouhal_lift_amplitude",
                _is_finite(cl_amplitude) and float(cl_amplitude) >= float(config["validation"]["min_cl_amplitude"]),
                f"cl_amplitude={cl_amplitude}, minimum={config['validation']['min_cl_amplitude']}",
            )

    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        _check(checks, f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local OpenFOAM C05 runtime and force-coefficient postprocess",
        "checks": checks,
    }
