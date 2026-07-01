from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.gmsh.boundary_layer_size_field_meshing.validation import (
    summarize_size_field_metrics,
    validate_size_field_contract,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/boundary_layer_size_field_meshing/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c05_validation_accepts_baseline_contract() -> None:
    config = _baseline_config()

    result = validate_size_field_contract(config)
    metrics = summarize_size_field_metrics(config, result)

    assert result["passed"] is True
    assert metrics["target_group_count"] == 1
    assert metrics["near_wall_element_count"] >= 24


def test_gmsh_c05_validation_rejects_missing_target_group() -> None:
    config = copy.deepcopy(_baseline_config())
    config["size_field"]["target_groups"] = ["inlet"]

    result = validate_size_field_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "size_field.target_groups" in failed


def test_gmsh_c05_validation_rejects_impossible_layer_parameters() -> None:
    config = copy.deepcopy(_baseline_config())
    config["size_field"]["growth_ratio"] = 1.0

    result = validate_size_field_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "size_field.layer_parameters" in failed


def test_gmsh_c05_validation_rejects_low_quality_proxy() -> None:
    config = copy.deepcopy(_baseline_config())
    config["expected_metrics"]["min_quality_proxy"] = 0.05

    result = validate_size_field_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "metrics.min_quality_proxy" in failed
