"""Validation for OpenFOAM C02 dry-run and runtime artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def validate_manifest(
    manifest: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    backend = manifest.get("backend", {})
    solver = manifest.get("solver", {})
    generated_files = set(manifest.get("generated_files", []))

    _check(checks, "backend.supported", backend.get("type") in {"dry_run_only", "wsl"}, f"backend={backend.get('type')!r}")
    _check(checks, "solver.potentialFoam", solver.get("name") == "potentialFoam", json.dumps(solver, ensure_ascii=False))
    _check(checks, "template.official_cylinder", "potentialFoam/cylinder" in config["template"]["source_path"], config["template"]["source_path"])
    _check(checks, "geometry.positive_radius", float(config["geometry"]["cylinder_radius_m"]) > 0.0, str(config["geometry"]["cylinder_radius_m"]))
    _check(checks, "material.positive_inlet_velocity", float(config["material"]["inlet_velocity_m_s"]) > 0.0, str(config["material"]["inlet_velocity_m_s"]))
    _check(checks, "material.positive_density", float(config["material"]["density_kg_m3"]) > 0.0, str(config["material"]["density_kg_m3"]))
    _check(
        checks,
        "reference.surface_cp_formula",
        config["analytical_reference"]["surface_cp_formula"] == "Cp(theta) = 1 - 4*sin(theta)^2",
        config["analytical_reference"]["surface_cp_formula"],
    )
    sample_sets = set(config["postprocess"]["sample_sets"])
    _check(
        checks,
        "postprocess.sample_sets.field",
        "cell_centres_excluding_near_cylinder_and_farfield_buffer" in sample_sets,
        json.dumps(sorted(sample_sets), ensure_ascii=False),
    )
    _check(
        checks,
        "postprocess.sample_sets.surface",
        "cylinder_patch_owner_cells" in sample_sets,
        json.dumps(sorted(sample_sets), ensure_ascii=False),
    )
    sample_policy = config["postprocess"]["sample_policy"]
    _check(
        checks,
        "postprocess.sample_policy.field_mask",
        sample_policy["field_mask"] == "cell_centres_excluding_near_cylinder_and_farfield_buffer",
        json.dumps(sample_policy, ensure_ascii=False),
    )
    _check(
        checks,
        "postprocess.sample_policy.surface_cp_source",
        sample_policy["surface_cp_source"] == "cylinder_patch_owner_cells" and sample_policy["owner_cell_proxy"] is True,
        json.dumps(sample_policy, ensure_ascii=False),
    )
    _check(
        checks,
        "postprocess.sample_policy.finite_domain_strategy",
        sample_policy["finite_domain_error_strategy"]
        in {"unbounded_analytic_solution_with_masked_sampling", "finite_domain_corrected_reference_required"},
        json.dumps(sample_policy, ensure_ascii=False),
    )
    error_norm_policy = config["postprocess"]["error_norm_policy"]
    _check(
        checks,
        "postprocess.error_norm_policy",
        error_norm_policy
        == {
            "velocity_norm": "componentwise_l2_linf_over_masked_cells",
            "pressure_norm": "kinematic_pressure_l2_over_masked_cells",
            "cp_norm": "surface_patch_owner_cell_linf",
        },
        json.dumps(error_norm_policy, ensure_ascii=False),
    )
    _check(
        checks,
        "function_objects.coded_error_disabled",
        config["function_objects"]["coded_error"]["enabled"] is False,
        json.dumps(config["function_objects"], ensure_ascii=False),
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
        "scope": "dry-run manifest and generated potentialFoam cylinder template case files only",
        "checks": checks,
    }


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    runtime_commands = metrics.get("runtime", {}).get("commands", [])
    solver = metrics.get("solver", {})
    analytical = metrics.get("postprocess", {}).get("analytical", {})

    for command in config["solver"]["command_sequence"]:
        match = next((item for item in runtime_commands if item.get("command") == command), None)
        _check(checks, f"command.{command}.returncode", bool(match and match.get("returncode") == 0), json.dumps(match or {}, ensure_ascii=False))

    _check(checks, "solver.started", solver.get("started") is True, "potentialFoam log signal found")
    _check(checks, "solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    residuals = solver.get("residual_history", [])
    _check(checks, "solver.residuals_present", bool(residuals), f"residual_count={len(residuals)}")

    field = analytical.get("field", {})
    cp = analytical.get("surface_cp", {})
    _check(checks, "postprocess.field_available", field.get("available") is True, json.dumps(field, ensure_ascii=False))
    _check(checks, "postprocess.cp_available", cp.get("available") is True, json.dumps(cp, ensure_ascii=False))

    velocity_l2 = field.get("velocity_l2_error")
    velocity_linf = field.get("velocity_linf_error")
    pressure_l2 = field.get("pressure_l2_error")
    cp_linf = cp.get("cp_linf_error")
    strategy = config["postprocess"]["sample_policy"]["finite_domain_error_strategy"]
    if strategy == "unbounded_analytic_solution_with_masked_sampling":
        _check(checks, "postprocess.velocity_l2_error", _is_finite(velocity_l2) and float(velocity_l2) <= float(config["validation"]["max_velocity_l2_error"]), f"value={velocity_l2}")
        _check(checks, "postprocess.velocity_linf_error", _is_finite(velocity_linf) and float(velocity_linf) <= float(config["validation"]["max_velocity_linf_error"]), f"value={velocity_linf}")
        _check(checks, "postprocess.pressure_l2_error", _is_finite(pressure_l2) and float(pressure_l2) <= float(config["validation"]["max_pressure_l2_error"]), f"value={pressure_l2}")
        _check(checks, "postprocess.cp_linf_error", _is_finite(cp_linf) and float(cp_linf) <= float(config["validation"]["max_cp_linf_error"]), f"value={cp_linf}")
    else:
        _check(
            checks,
            "postprocess.finite_domain_reference_required",
            all(_is_finite(value) for value in [velocity_l2, velocity_linf, pressure_l2, cp_linf]),
            json.dumps({"strategy": strategy, "velocity_l2_error": velocity_l2, "velocity_linf_error": velocity_linf, "pressure_l2_error": pressure_l2, "cp_linf_error": cp_linf}, ensure_ascii=False),
        )

    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        _check(checks, f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local OpenFOAM C02 runtime and analytical potential-flow postprocess"
        if config["postprocess"]["sample_policy"]["finite_domain_error_strategy"] == "unbounded_analytic_solution_with_masked_sampling"
        else "local OpenFOAM C02 runtime diagnostic; finite-domain corrected reference is required before analytical validation",
        "checks": checks,
    }
