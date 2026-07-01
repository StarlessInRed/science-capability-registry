from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.gmsh.mesh_refinement_quality_trend.validation import (
    summarize_refinement_metrics,
    validate_refinement_trend,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/mesh_refinement_quality_trend/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c03_validation_accepts_baseline_trend() -> None:
    config = _baseline_config()

    result = validate_refinement_trend(config)
    metrics = summarize_refinement_metrics(config, result)

    assert result["passed"] is True
    assert metrics["level_count"] == 3
    assert metrics["element_count_monotonic"] is True


def test_gmsh_c03_validation_rejects_nonmonotonic_element_count() -> None:
    config = copy.deepcopy(_baseline_config())
    config["refinement_levels"][2]["expected_element_count_min"] = 200

    result = validate_refinement_trend(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "trend.element_count_increases" in failed


def test_gmsh_c03_validation_rejects_low_quality_proxy() -> None:
    config = copy.deepcopy(_baseline_config())
    config["refinement_levels"][1]["expected_min_quality_proxy"] = 0.05

    result = validate_refinement_trend(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "quality.min_quality_proxy" in failed


def test_gmsh_c03_validation_rejects_nonfinite_coordinates() -> None:
    config = copy.deepcopy(_baseline_config())
    config["refinement_levels"][1]["nonfinite_coordinate_count"] = 1

    result = validate_refinement_trend(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "quality.nonfinite_coordinates" in failed
