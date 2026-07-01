"""Validation for Gmsh C04 CAD import and healing contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_cad_healing_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    entity_expectations = config["entity_map_expectations"]
    rebinding = config["physical_group_rebinding"]
    imported_entities = entity_expectations["imported_entities"]
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "imported_entity_count": sum(int(value) for value in imported_entities.values()),
        "imported_surface_count": int(imported_entities["surfaces"]),
        "healed_entity_count": int(entity_expectations["modified_entity_count"]) + int(entity_expectations["new_entity_count"]),
        "deleted_entity_count": int(entity_expectations["deleted_entity_count"]),
        "duplicate_or_sliver_count": int(rebinding["duplicate_or_sliver_count"]),
        "unassigned_entity_count": int(rebinding["unassigned_entity_count"]),
        "critical_face_count": len(entity_expectations["critical_faces"]),
        "enabled_healing_operation_count": sum(1 for item in config["healing_operations"] if item["enabled"]),
    }
    if validation is not None:
        result["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return result


def validate_cad_healing_contract(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    metrics = summarize_cad_healing_metrics(config)
    critical_faces = config["entity_map_expectations"]["critical_faces"]
    critical_groups = {face["physical_group"] for face in critical_faces if face["assigned"]}
    unassigned_critical_faces = [face["entity_id"] for face in critical_faces if not face["assigned"]]
    required_groups = set(config["validation"]["required_physical_groups"])
    rebinding_required_groups = set(config["physical_group_rebinding"]["required_groups"])
    thresholds = config["meshability_thresholds"]

    _check(
        checks,
        "healing_operations.enabled",
        metrics["enabled_healing_operation_count"] > 0,
        json.dumps(config["healing_operations"], ensure_ascii=False),
    )
    _check(
        checks,
        "entity_map.imported_entities",
        metrics["imported_entity_count"] > 0 and metrics["imported_surface_count"] > 0,
        json.dumps(config["entity_map_expectations"]["imported_entities"], ensure_ascii=False),
    )
    _check(
        checks,
        "entity_map.critical_faces_assigned",
        not unassigned_critical_faces,
        json.dumps({"unassigned_critical_faces": unassigned_critical_faces}, ensure_ascii=False),
    )
    _check(
        checks,
        "physical_group_rebinding.required_groups",
        required_groups.issubset(critical_groups) and required_groups.issubset(rebinding_required_groups),
        json.dumps(
            {
                "critical_groups": sorted(critical_groups),
                "rebinding_required_groups": sorted(rebinding_required_groups),
                "required_groups": sorted(required_groups),
            },
            ensure_ascii=False,
        ),
    )
    _check(
        checks,
        "meshability.unassigned_entities",
        metrics["unassigned_entity_count"] <= int(thresholds["max_unassigned_entity_count"]),
        json.dumps({"unassigned_entity_count": metrics["unassigned_entity_count"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "meshability.duplicate_or_sliver",
        metrics["duplicate_or_sliver_count"] <= int(thresholds["max_duplicate_or_sliver_count"]),
        json.dumps({"duplicate_or_sliver_count": metrics["duplicate_or_sliver_count"]}, ensure_ascii=False),
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh CAD import and healing contract; no OpenCASCADE import or mesh generation",
        "checks": checks,
        "details": {
            "critical_groups": sorted(critical_groups),
            "unassigned_critical_faces": unassigned_critical_faces,
            "metrics": metrics,
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_cad_healing_contract(config)
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
        "scope": "Gmsh CAD healing manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
