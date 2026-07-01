from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.gmsh.cad_import_geometry_healing.validation import (
    summarize_cad_healing_metrics,
    validate_cad_healing_contract,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/cad_import_geometry_healing/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c04_validation_accepts_baseline_contract() -> None:
    config = _baseline_config()

    result = validate_cad_healing_contract(config)
    metrics = summarize_cad_healing_metrics(config, result)

    assert result["passed"] is True
    assert metrics["imported_surface_count"] == 1
    assert metrics["enabled_healing_operation_count"] == 2


def test_gmsh_c04_validation_rejects_unassigned_critical_face() -> None:
    config = copy.deepcopy(_baseline_config())
    config["entity_map_expectations"]["critical_faces"][1]["assigned"] = False
    config["physical_group_rebinding"]["unassigned_entity_count"] = 1

    result = validate_cad_healing_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "entity_map.critical_faces_assigned" in failed
    assert "meshability.unassigned_entities" in failed


def test_gmsh_c04_validation_rejects_missing_physical_group_rebinding() -> None:
    config = copy.deepcopy(_baseline_config())
    config["physical_group_rebinding"]["required_groups"].remove("wall")

    result = validate_cad_healing_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "physical_group_rebinding.required_groups" in failed


def test_gmsh_c04_validation_rejects_duplicate_or_sliver_entities() -> None:
    config = copy.deepcopy(_baseline_config())
    config["physical_group_rebinding"]["duplicate_or_sliver_count"] = 2

    result = validate_cad_healing_contract(config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "meshability.duplicate_or_sliver" in failed
