"""Validation helpers for Fluent C02 verification references."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_reference_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    values = config["reference_values"]
    inputs = config["reference_formula"]["pressure_drop_inputs"]
    computed_pressure_drop = (
        32.0
        * inputs["dynamic_viscosity_kg_m_s"]
        * inputs["length_m"]
        * inputs["mean_velocity_m_s"]
        / (inputs["diameter_m"] ** 2)
    )
    formula_relative_error = abs(computed_pressure_drop - values["target_pressure_drop_pa"]) / values["target_pressure_drop_pa"]
    manual_relative_error = (
        abs(values["manual_fluent_pressure_drop_pa"] - values["target_pressure_drop_pa"])
        / values["target_pressure_drop_pa"]
    )
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "manual_case_id": config["reference_source"]["manual_case_id"],
        "computed_formula_pressure_drop_pa": computed_pressure_drop,
        "target_pressure_drop_pa": values["target_pressure_drop_pa"],
        "manual_fluent_pressure_drop_pa": values["manual_fluent_pressure_drop_pa"],
        "formula_relative_error": formula_relative_error,
        "manual_relative_error": manual_relative_error,
        "manual_fluent_ratio": values["manual_fluent_ratio"],
        "runnable_payload_status": config["reference_source"]["runnable_payload_status"],
        "quantity": values["quantity"],
        "unit": values["unit"],
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def summarize_mesh_runtime_metrics(config: dict[str, Any], runtime_metrics: dict[str, Any]) -> dict[str, Any]:
    result = summarize_reference_metrics(config)
    result.update(runtime_metrics)
    return result


def validate_reference_contract(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    metrics = summarize_reference_metrics(config)
    geometry = config["geometry"]
    source = config["reference_source"]

    _check(
        checks,
        "reference.source_case_selected",
        source["manual_case_id"] == "VMFL005" and bool(source["manual_case_title"]),
        json.dumps(source, ensure_ascii=False),
    )
    _check(
        checks,
        "reference.geometry_pipe",
        geometry["length_m"] > 0.0 and geometry["radius_m"] > 0.0,
        json.dumps(geometry, ensure_ascii=False),
    )
    _check(
        checks,
        "reference.boundary_conditions_declared",
        config["boundary_conditions"]["inlet_average_velocity_m_s"] > 0.0
        and bool(config["boundary_conditions"]["inlet_profile"])
        and bool(config["boundary_conditions"]["wall"])
        and bool(config["boundary_conditions"]["axis"])
        and bool(config["boundary_conditions"]["outlet_closure"]),
        json.dumps(config["boundary_conditions"], ensure_ascii=False),
    )
    _check(
        checks,
        "reference.formula_matches_geometry",
        math.isclose(config["reference_formula"]["pressure_drop_inputs"]["diameter_m"], 2.0 * geometry["radius_m"]),
        json.dumps(config["reference_formula"], ensure_ascii=False),
    )
    _check(
        checks,
        "reference.formula_recomputes_target",
        metrics["formula_relative_error"] <= 1.0e-12,
        f"{metrics['formula_relative_error']} <= 1e-12",
    )
    _check(
        checks,
        "reference.manual_target_error",
        metrics["manual_relative_error"] <= config["validation"]["max_manual_relative_error"],
        f"{metrics['manual_relative_error']} <= {config['validation']['max_manual_relative_error']}",
    )
    _check(
        checks,
        "reference.payload_status_explicit",
        source["runnable_payload_status"] == "not_found_in_current_library",
        source["runnable_payload_status"],
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C02 verification-manual reference mapping; no Fluent execution",
        "checks": checks,
        "details": {
            "metrics": metrics,
            "no_claims": config["validation"]["no_claims"],
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_reference_contract(config)
    checks = list(validation["checks"])

    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)

    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            _check(checks, f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C02 reference manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }


def validate_mesh_runtime_smoke(
    manifest: dict[str, Any],
    config: dict[str, Any],
    metrics: dict[str, Any],
    output_dir: str | Path,
    check_artifacts: bool = True,
) -> dict[str, Any]:
    validation = validate_manifest(manifest, config, output_dir if check_artifacts else None)
    checks = list(validation["checks"])
    mesh = config["mesh_generation"]
    expected_cells = mesh["axial_cells"] * mesh["radial_cells"]
    face_counts = metrics["mesh_face_counts"]
    required_face_zones = ["axis", "interior", "pressure-outlet", "velocity-inlet", "wall"]

    _check(
        checks,
        "runtime.return_code_zero",
        metrics["fluent_return_code"] == 0,
        str(metrics["fluent_return_code"]),
    )
    _check(
        checks,
        "runtime.mesh_check_completed",
        bool(metrics["mesh_check_completed"]),
        str(metrics["mesh_check_completed"]),
    )
    _check(
        checks,
        "runtime.no_fluent_errors",
        metrics["fluent_error_count"] == 0,
        str(metrics["fluent_error_count"]),
    )
    _check(
        checks,
        "runtime.cells_match_mesh_config",
        metrics["mesh_cell_count"] == expected_cells,
        f"{metrics['mesh_cell_count']} == {expected_cells}",
    )
    for zone_name in required_face_zones:
        _check(
            checks,
            f"runtime.face_zone.{zone_name}",
            zone_name in face_counts and face_counts[zone_name] > 0,
            json.dumps(face_counts, ensure_ascii=False, sort_keys=True),
        )
    _check(
        checks,
        "runtime.warning_budget",
        metrics["fluent_warning_count"] <= config["runtime_smoke"]["max_warning_count"],
        f"{metrics['fluent_warning_count']} <= {config['runtime_smoke']['max_warning_count']}",
    )
    _check(
        checks,
        "runtime.pressure_drop_not_claimed",
        metrics["pressure_drop_runtime_status"] == "not_extracted_in_mesh_smoke",
        metrics["pressure_drop_runtime_status"],
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C02 self-generated VMFL005 mesh-readability smoke; pressure-drop solve not claimed",
        "checks": checks,
        "details": {
            "metrics": metrics,
            "no_claims": config["validation"]["no_claims"],
            "allowed_runtime_warnings": config["runtime_smoke"]["allowed_warning_fragments"],
        },
    }
