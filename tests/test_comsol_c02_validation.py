from __future__ import annotations

import copy
from pathlib import Path

import yaml

from science_capability_registry.comsol.model_construction_api_contract.config import validate_case_config
from science_capability_registry.comsol.model_construction_api_contract.validation import (
    duplicate_tag_count,
    finite_parameter_count,
    validate_metrics,
)

CONFIG_PATH = Path("configs/comsol/model_construction_api_contract/local_livelink_model_tree_smoke.yaml")


def _config() -> dict:
    return validate_case_config(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")))


def test_comsol_c02_duplicate_tag_count_detects_collision() -> None:
    config = _config()
    config["model_tree"]["tags"]["study_tag"] = config["model_tree"]["tags"]["mesh_tag"]

    assert duplicate_tag_count(config) == 1


def test_comsol_c02_finite_parameter_count_accepts_numeric_manifest() -> None:
    config = _config()
    manifest = {
        "parameter_values": {
            "c02_width": 1.0,
            "c02_height": 0.5,
            "c02_k": 1.0,
        }
    }

    assert finite_parameter_count(config, manifest) == 3


def test_comsol_c02_validation_rejects_solver_execution(tmp_path: Path) -> None:
    config = _config()
    metrics = {
        "validated_config": True,
        "script_generated": True,
        "script_file": "matlab_model_construction_smoke.m",
        "environment_summary": {
            "required_count": 3,
            "required_configured_count": 3,
            "required_existing_count": 3,
            "all_required_configured": True,
            "all_required_paths_exist": True,
        },
        "matlab_return_code": 0,
        "model_tree_manifest_written": True,
        "construction_manifest_written": True,
        "parameter_count": 3,
        "finite_parameter_count": 3,
        "required_tag_missing_count": 0,
        "missing_required_tags": [],
        "duplicate_tag_count": 0,
        "solver_executed": True,
        "runtime_status": "matlab_livelink_model_tree_passed",
    }

    validation = validate_metrics(metrics, config, tmp_path, check_artifacts=False)

    assert validation["passed"] is False
    assert any(item["name"] == "solver.not_executed" and not item["passed"] for item in validation["checks"])


def test_comsol_c02_validation_rejects_missing_required_tag(tmp_path: Path) -> None:
    config = _config()
    metrics = copy.deepcopy(
        {
            "validated_config": True,
            "script_generated": True,
            "script_file": "matlab_model_construction_smoke.m",
            "environment_summary": {
                "required_count": 3,
                "required_configured_count": 3,
                "required_existing_count": 3,
                "all_required_configured": True,
                "all_required_paths_exist": True,
            },
            "matlab_return_code": 0,
            "model_tree_manifest_written": True,
            "construction_manifest_written": True,
            "parameter_count": 3,
            "finite_parameter_count": 3,
            "required_tag_missing_count": 1,
            "missing_required_tags": ["mesh_tag"],
            "duplicate_tag_count": 0,
            "solver_executed": False,
            "runtime_status": "matlab_livelink_model_tree_passed",
        }
    )

    validation = validate_metrics(metrics, config, tmp_path, check_artifacts=False)

    assert validation["passed"] is False
    assert any(item["name"] == "model_tags.required_present" and not item["passed"] for item in validation["checks"])
