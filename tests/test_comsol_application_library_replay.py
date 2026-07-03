from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from science_capability_registry.comsol.application_library_replay import (
    SCHEMA_PATH,
    run,
    validate_application_library_metrics,
)

CONFIGS = [
    Path("configs/comsol/application_library_replay/domain_activation_official_replay_smoke.yaml"),
    Path("configs/comsol/application_library_replay/pseudoperiodicity_official_replay_export_smoke.yaml"),
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_comsol_application_library_replay_configs_match_schema() -> None:
    schema = _read_json(SCHEMA_PATH)
    failures = {}
    for config_path in CONFIGS:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(_read_yaml(config_path)),
            key=lambda error: list(error.path),
        )
        if errors:
            failures[config_path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_comsol_application_library_replay_schema_rejects_absolute_path() -> None:
    config = copy.deepcopy(_read_yaml(CONFIGS[0]))
    config["replay"]["model_file"] = "G:/COMSOL63/Multiphysics/applications/model.mph"

    errors = list(Draft202012Validator(_read_json(SCHEMA_PATH)).iter_errors(config))

    assert errors


def test_comsol_application_library_replay_dry_run_writes_contract(tmp_path: Path) -> None:
    result = run(config_path=CONFIGS[0], output_dir=tmp_path, dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["validation"]["gate"] == "static-readiness"
    assert result["metrics"]["runtime_status"] == "dry_run_not_executed"
    assert result["covers_capabilities"] == [
        "C03_geometry_mesh_import_contract",
        "C04_physics_boundary_assignment_contract",
        "C05_study_run_solver_smoke",
        "C06_result_extraction_postprocess_validation",
    ]
    for rel_path in [
        "source_manifest.json",
        "selection_map.json",
        "physics_assignment_manifest.json",
        "boundary_assignment_manifest.json",
        "solver_manifest.json",
        "dataset_manifest.json",
        "export_manifest.json",
        "probes.csv",
        "units.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "matlab_domain_activation_official_replay.m",
    ]:
        assert (tmp_path / rel_path).exists(), rel_path
    script_text = (tmp_path / "matlab_domain_activation_official_replay.m").read_text(encoding="ascii")
    assert "COMSOL_APPLICATION_LIBRARY_ROOT" in script_text
    assert "mphopen(modelPath)" in script_text


def test_comsol_application_library_replay_runtime_validation_rejects_missing_outputs(tmp_path: Path) -> None:
    config = _read_yaml(CONFIGS[0])
    metrics = {
        "validated_config": True,
        "script_generated": True,
        "script_file": "matlab_domain_activation_official_replay.m",
        "runtime_status": "matlab_livelink_application_library_replay_failed",
        "environment_summary": {
            "required_count": 4,
            "required_configured_count": 4,
            "required_existing_count": 4,
            "all_required_configured": True,
            "all_required_paths_exist": True,
        },
        "source_file_count": 2,
        "source_files_existing_count": 2,
        "covers_capability_count": 4,
        "matlab_return_code": 1,
        "selection_role_count": 0,
        "physics_created": False,
        "missing_boundary_assignment_count": 1,
        "solver_completed": False,
        "dataset_count": 0,
        "exported_probe_count": 0,
        "finite_value_fraction": 0.0,
        "missing_unit_count": 1,
    }

    validation = validate_application_library_metrics(metrics, config, tmp_path, check_artifacts=False)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}

    assert validation["passed"] is False
    assert "matlab.return_code" in failed
    assert "selection.roles_declared" in failed
    assert "solver.completed" in failed
    assert "probe.values_finite" in failed
