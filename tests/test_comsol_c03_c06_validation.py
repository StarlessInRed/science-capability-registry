from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from science_capability_registry.comsol.geometry_mesh_import_contract import run as run_c03
from science_capability_registry.comsol.heat_rectangle_livelink import validate_heat_rectangle_metrics
from science_capability_registry.comsol.static_contract import REPO_ROOT, validate_static_manifest

C03_CONFIG = Path("configs/comsol/geometry_mesh_import_contract/static_contract.yaml")
C03_SCHEMA = REPO_ROOT / "schemas/comsol_C03_geometry_mesh_import_contract.schema.json"

RUNTIME_CONFIGS = {
    "geometry_mesh_import_contract": Path(
        "configs/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle.yaml"
    ),
    "physics_boundary_assignment_contract": Path(
        "configs/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle.yaml"
    ),
    "study_run_solver_smoke": Path("configs/comsol/study_run_solver_smoke/local_livelink_heat_rectangle.yaml"),
    "result_extraction_postprocess_validation": Path(
        "configs/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle.yaml"
    ),
}


def test_comsol_static_validation_rejects_missing_required_role() -> None:
    config = yaml.safe_load(C03_CONFIG.read_text(encoding="utf-8"))
    config["contract"]["declared_objects"] = [
        item for item in config["contract"]["declared_objects"] if item["role"] != "selection_map"
    ]
    manifest = {
        "validated_config": True,
        "runtime_executed": False,
        "backend": config["backend"],
        "contract": config["contract"],
        "generated_files": config["outputs"]["expected_outputs"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
    }

    validation = validate_static_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "object_role.present.selection_map" and not item["passed"] for item in validation["checks"])


def test_comsol_static_runner_rejects_non_dry_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="dry_run only"):
        run_c03(config_path=C03_CONFIG, output_dir=tmp_path, dry_run=False)


def _runtime_config(stage: str) -> dict[str, Any]:
    config = yaml.safe_load(RUNTIME_CONFIGS[stage].read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    return config


def _runtime_metrics(stage: str) -> dict[str, Any]:
    return {
        "validated_config": True,
        "script_generated": True,
        "script_file": "matlab_smoke.m",
        "environment_summary": {
            "required_count": 3,
            "required_configured_count": 3,
            "required_existing_count": 3,
            "all_required_configured": True,
            "all_required_paths_exist": True,
        },
        "runtime_status": f"{stage}_passed",
        "matlab_return_code": 0,
        "geometry_created": True,
        "mesh_created": True,
        "selection_role_count": 1,
        "material_assigned": True,
        "physics_created": True,
        "boundary_assignment_count": 1,
        "missing_boundary_assignment_count": 0,
        "missing_unit_count": 0,
        "study_executed": stage in {"study_run_solver_smoke", "result_extraction_postprocess_validation"},
        "solver_completed": stage in {"study_run_solver_smoke", "result_extraction_postprocess_validation"},
        "dataset_count": 1 if stage in {"study_run_solver_smoke", "result_extraction_postprocess_validation"} else 0,
        "exported_probe_count": 1 if stage == "result_extraction_postprocess_validation" else 0,
        "finite_value_fraction": 1.0 if stage == "result_extraction_postprocess_validation" else 0.0,
        "max_abs_temperature_error_K": 0.0 if stage == "result_extraction_postprocess_validation" else None,
        "solver_executed": stage in {"study_run_solver_smoke", "result_extraction_postprocess_validation"},
    }


def _failed_check_names(validation: dict[str, Any]) -> set[str]:
    return {item["name"] for item in validation["checks"] if not item["passed"]}


def test_comsol_c03_runtime_validation_rejects_missing_selection_role(tmp_path: Path) -> None:
    stage = "geometry_mesh_import_contract"
    metrics = _runtime_metrics(stage)
    metrics["selection_role_count"] = 0

    validation = validate_heat_rectangle_metrics(metrics, _runtime_config(stage), tmp_path, stage, check_artifacts=False)

    assert validation["passed"] is False
    assert "selection.roles_declared" in _failed_check_names(validation)


def test_comsol_c04_runtime_validation_rejects_missing_assignment_and_units(tmp_path: Path) -> None:
    stage = "physics_boundary_assignment_contract"
    metrics = _runtime_metrics(stage)
    metrics["missing_boundary_assignment_count"] = 1
    metrics["missing_unit_count"] = 1

    validation = validate_heat_rectangle_metrics(metrics, _runtime_config(stage), tmp_path, stage, check_artifacts=False)

    failed = _failed_check_names(validation)
    assert validation["passed"] is False
    assert "boundary.assignments_complete" in failed
    assert "units.present" in failed


def test_comsol_c05_runtime_validation_rejects_solver_failure(tmp_path: Path) -> None:
    stage = "study_run_solver_smoke"
    metrics = _runtime_metrics(stage)
    metrics["matlab_return_code"] = 1
    metrics["solver_completed"] = False
    metrics["dataset_count"] = 0

    validation = validate_heat_rectangle_metrics(metrics, _runtime_config(stage), tmp_path, stage, check_artifacts=False)

    failed = _failed_check_names(validation)
    assert validation["passed"] is False
    assert "solver.completed" in failed
    assert "dataset.present" in failed
    assert "matlab.return_code" in failed


def test_comsol_c06_runtime_validation_rejects_nonfinite_probe_and_missing_units(tmp_path: Path) -> None:
    stage = "result_extraction_postprocess_validation"
    metrics = _runtime_metrics(stage)
    metrics["finite_value_fraction"] = 0.0
    metrics["missing_unit_count"] = 1
    metrics["max_abs_temperature_error_K"] = None

    validation = validate_heat_rectangle_metrics(metrics, _runtime_config(stage), tmp_path, stage, check_artifacts=False)

    failed = _failed_check_names(validation)
    assert validation["passed"] is False
    assert "probe.values_finite" in failed
    assert "units.present" in failed
    assert "probe.expected_constant_temperature" in failed
