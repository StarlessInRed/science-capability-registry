from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.gmsh.multi_solver_mesh_export_contract.validation import (
    summarize_export_metrics,
    validate_export_contract,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/multi_solver_mesh_export_contract/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c06_validation_accepts_baseline_contract() -> None:
    config = _baseline_config()

    result = validate_export_contract(config)
    metrics = summarize_export_metrics(config, result)

    assert result["passed"] is True
    assert metrics["target_count"] == 2
    assert metrics["solver_family_count"] == 2


def test_gmsh_c06_validation_rejects_missing_target() -> None:
    config = copy.deepcopy(_baseline_config())
    config["export_targets"] = [config["export_targets"][0]]

    result = validate_export_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "export_targets.required_ids" in failed
    assert "export_targets.solver_family_count" in failed


def test_gmsh_c06_validation_rejects_boundary_name_mismatch() -> None:
    config = copy.deepcopy(_baseline_config())
    config["export_targets"][0]["expected_boundary_names"].remove("outlet")

    result = validate_export_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "export_targets.boundary_names" in failed


def test_gmsh_c06_validation_rejects_unit_scale_mismatch() -> None:
    config = copy.deepcopy(_baseline_config())
    config["unit_policy"]["scale_factor"] = 1000.0

    result = validate_export_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "unit_policy.scale_factor" in failed
