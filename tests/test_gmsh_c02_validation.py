from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.gmsh.boundary_physical_group_contract.validation import (
    summarize_contract_metrics,
    validate_boundary_contract,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/boundary_physical_group_contract/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c02_validation_accepts_baseline_contract() -> None:
    config = _baseline_config()

    result = validate_boundary_contract(config)
    metrics = summarize_contract_metrics(config, result)

    assert result["passed"] is True
    assert metrics["physical_group_count"] == 4
    assert metrics["role_mapping_coverage"] == 1.0


def test_gmsh_c02_validation_rejects_missing_required_group() -> None:
    config = copy.deepcopy(_baseline_config())
    config["physical_groups"] = [item for item in config["physical_groups"] if item["name"] != "outlet"]

    result = validate_boundary_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "physical_groups.required_names" in failed
    assert "physical_groups.required_roles" in failed


def test_gmsh_c02_validation_rejects_dimension_role_mismatch() -> None:
    config = copy.deepcopy(_baseline_config())
    for group in config["physical_groups"]:
        if group["name"] == "wall":
            group["dimension"] = 2

    result = validate_boundary_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "physical_groups.dimension_role" in failed


def test_gmsh_c02_validation_rejects_duplicate_names() -> None:
    config = copy.deepcopy(_baseline_config())
    duplicate = copy.deepcopy(config["physical_groups"][0])
    duplicate["role"] = "outlet"
    config["physical_groups"].append(duplicate)

    result = validate_boundary_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "physical_groups.duplicate_names" in failed


def test_gmsh_c02_validation_rejects_downstream_role_gap() -> None:
    config = copy.deepcopy(_baseline_config())
    del config["downstream_boundary_map"]["role_to_boundary_type"]["outlet"]

    result = validate_boundary_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "downstream_boundary_map.required_role_coverage" in failed
