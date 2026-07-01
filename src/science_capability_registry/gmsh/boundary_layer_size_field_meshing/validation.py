"""Validation for Gmsh C05 boundary-layer size-field contracts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_size_field_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    expected = config["expected_metrics"]
    size_field = config["size_field"]
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "target_group_count": len(size_field["target_groups"]),
        "near_wall_element_count": int(expected["near_wall_element_count"]),
        "min_near_wall_spacing_m": float(expected["min_near_wall_spacing_m"]),
        "max_growth_ratio_observed": float(expected["max_growth_ratio_observed"]),
        "min_quality_proxy": float(expected["min_quality_proxy"]),
        "configured_first_layer_height_m": float(size_field["first_layer_height_m"]),
        "configured_growth_ratio": float(size_field["growth_ratio"]),
        "configured_total_thickness_m": float(size_field["total_thickness_m"]),
    }
    if validation is not None:
        result["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return result


def validate_size_field_contract(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    size_field = config["size_field"]
    thresholds = config["quality_thresholds"]
    metrics = summarize_size_field_metrics(config)
    target_groups = set(size_field["target_groups"])
    required_target_groups = set(config["validation"]["required_target_groups"])
    first_layer = float(size_field["first_layer_height_m"])
    growth_ratio = float(size_field["growth_ratio"])
    total_thickness = float(size_field["total_thickness_m"])
    far_field_size = float(size_field["far_field_size_m"])

    _check(
        checks,
        "size_field.target_groups",
        required_target_groups.issubset(target_groups),
        f"target_groups={sorted(target_groups)}, required={sorted(required_target_groups)}",
    )
    _check(
        checks,
        "size_field.layer_parameters",
        first_layer > 0 and growth_ratio > 1 and total_thickness > first_layer and far_field_size >= total_thickness,
        json.dumps(size_field, ensure_ascii=False),
    )
    _check(
        checks,
        "metrics.near_wall_element_count",
        int(metrics["near_wall_element_count"]) >= int(thresholds["min_near_wall_element_count"]),
        json.dumps({"near_wall_element_count": metrics["near_wall_element_count"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "metrics.min_near_wall_spacing",
        math.isfinite(metrics["min_near_wall_spacing_m"])
        and metrics["min_near_wall_spacing_m"] >= float(thresholds["min_near_wall_spacing_m"]),
        json.dumps({"min_near_wall_spacing_m": metrics["min_near_wall_spacing_m"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "metrics.max_growth_ratio",
        math.isfinite(metrics["max_growth_ratio_observed"])
        and metrics["max_growth_ratio_observed"] <= float(thresholds["max_growth_ratio_observed"]),
        json.dumps({"max_growth_ratio_observed": metrics["max_growth_ratio_observed"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "metrics.min_quality_proxy",
        math.isfinite(metrics["min_quality_proxy"])
        and metrics["min_quality_proxy"] >= float(thresholds["min_quality_proxy"]),
        json.dumps({"min_quality_proxy": metrics["min_quality_proxy"]}, ensure_ascii=False),
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh boundary-layer and size-field contract; no mesh generation or solver y+ validation",
        "checks": checks,
        "details": {
            "target_groups": sorted(target_groups),
            "required_target_groups": sorted(required_target_groups),
            "metrics": metrics,
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_size_field_contract(config)
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
        "scope": "Gmsh size-field manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
