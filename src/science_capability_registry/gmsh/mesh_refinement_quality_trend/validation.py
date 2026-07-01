"""Validation for Gmsh C03 refinement and quality trend contracts."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple


class RefinementLevel(NamedTuple):
    level_id: str
    characteristic_length_m: float
    expected_node_count_min: int
    expected_element_count_min: int
    expected_min_quality_proxy: float
    expected_max_aspect_ratio_proxy: float
    nonfinite_coordinate_count: int

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RefinementLevel":
        return cls(
            level_id=str(data["level_id"]),
            characteristic_length_m=float(data["characteristic_length_m"]),
            expected_node_count_min=int(data["expected_node_count_min"]),
            expected_element_count_min=int(data["expected_element_count_min"]),
            expected_min_quality_proxy=float(data["expected_min_quality_proxy"]),
            expected_max_aspect_ratio_proxy=float(data["expected_max_aspect_ratio_proxy"]),
            nonfinite_coordinate_count=int(data["nonfinite_coordinate_count"]),
        )


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _levels(config: dict[str, Any]) -> list[RefinementLevel]:
    return [RefinementLevel.from_mapping(item) for item in config["refinement_levels"]]


def _strictly_increasing(values: list[float | int]) -> bool:
    return all(next_value > value for value, next_value in zip(values, values[1:]))


def _strictly_decreasing(values: list[float | int]) -> bool:
    return all(next_value < value for value, next_value in zip(values, values[1:]))


def summarize_refinement_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    levels = _levels(config)
    quality_values = [level.expected_min_quality_proxy for level in levels]
    quality_drop = max(quality_values) - min(quality_values) if quality_values else 0.0
    quality_drop_fraction = quality_drop / max(quality_values) if quality_values and max(quality_values) > 0 else 0.0
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "level_count": len(levels),
        "first_level_id": levels[0].level_id if levels else None,
        "last_level_id": levels[-1].level_id if levels else None,
        "node_count_monotonic": _strictly_increasing([level.expected_node_count_min for level in levels]),
        "element_count_monotonic": _strictly_increasing([level.expected_element_count_min for level in levels]),
        "characteristic_length_monotonic": _strictly_decreasing([level.characteristic_length_m for level in levels]),
        "min_quality_proxy": min(quality_values) if quality_values else None,
        "max_aspect_ratio_proxy": max(level.expected_max_aspect_ratio_proxy for level in levels) if levels else None,
        "nonfinite_coordinate_count": sum(level.nonfinite_coordinate_count for level in levels),
        "quality_drop_fraction": quality_drop_fraction,
    }
    if validation is not None:
        result["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return result


def validate_refinement_trend(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    levels = _levels(config)
    level_ids = [level.level_id for level in levels]
    required_level_ids = set(config["validation"]["required_level_ids"])
    duplicate_level_ids = sorted(level_id for level_id, count in Counter(level_ids).items() if count > 1)
    thresholds = config["quality_thresholds"]
    metrics = summarize_refinement_metrics(config)

    _check(
        checks,
        "refinement_levels.required_ids",
        required_level_ids.issubset(set(level_ids)),
        f"levels={sorted(level_ids)}, required={sorted(required_level_ids)}",
    )
    _check(
        checks,
        "refinement_levels.duplicate_ids",
        not duplicate_level_ids,
        json.dumps({"duplicates": duplicate_level_ids}, ensure_ascii=False),
    )
    _check(
        checks,
        "trend.characteristic_length_decreases",
        metrics["characteristic_length_monotonic"],
        json.dumps([level.characteristic_length_m for level in levels], ensure_ascii=False),
    )
    _check(
        checks,
        "trend.node_count_increases",
        metrics["node_count_monotonic"],
        json.dumps([level.expected_node_count_min for level in levels], ensure_ascii=False),
    )
    _check(
        checks,
        "trend.element_count_increases",
        metrics["element_count_monotonic"],
        json.dumps([level.expected_element_count_min for level in levels], ensure_ascii=False),
    )
    _check(
        checks,
        "quality.min_quality_proxy",
        isinstance(metrics["min_quality_proxy"], (int, float))
        and math.isfinite(float(metrics["min_quality_proxy"]))
        and float(metrics["min_quality_proxy"]) >= float(thresholds["min_quality_proxy"]),
        json.dumps({"min_quality_proxy": metrics["min_quality_proxy"], "threshold": thresholds["min_quality_proxy"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "quality.max_aspect_ratio_proxy",
        isinstance(metrics["max_aspect_ratio_proxy"], (int, float))
        and math.isfinite(float(metrics["max_aspect_ratio_proxy"]))
        and float(metrics["max_aspect_ratio_proxy"]) <= float(thresholds["max_aspect_ratio_proxy"]),
        json.dumps({"max_aspect_ratio_proxy": metrics["max_aspect_ratio_proxy"], "threshold": thresholds["max_aspect_ratio_proxy"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "quality.nonfinite_coordinates",
        int(metrics["nonfinite_coordinate_count"]) <= int(thresholds["max_nonfinite_coordinate_count"]),
        json.dumps({"nonfinite_coordinate_count": metrics["nonfinite_coordinate_count"]}, ensure_ascii=False),
    )
    _check(
        checks,
        "quality.drop_fraction",
        float(metrics["quality_drop_fraction"]) <= float(config["trend_expectations"]["max_quality_drop_fraction"]),
        json.dumps({"quality_drop_fraction": metrics["quality_drop_fraction"]}, ensure_ascii=False),
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh mesh refinement and quality trend contract; no mesh generation or solver execution",
        "checks": checks,
        "details": {
            "level_ids": level_ids,
            "duplicate_level_ids": duplicate_level_ids,
            "metrics": metrics,
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_refinement_trend(config)
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
        "scope": "Gmsh refinement trend manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
