from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

CASES = [
    (
        Path("schemas/comsol_C03_geometry_mesh_import_contract.schema.json"),
        Path("configs/comsol/geometry_mesh_import_contract/static_contract.yaml"),
    ),
    (
        Path("schemas/comsol_C04_physics_boundary_assignment_contract.schema.json"),
        Path(
            "configs/comsol/physics_boundary_assignment_contract/static_contract.yaml"
        ),
    ),
    (
        Path("schemas/comsol_C05_study_run_solver_smoke.schema.json"),
        Path("configs/comsol/study_run_solver_smoke/static_contract.yaml"),
    ),
    (
        Path("schemas/comsol_C06_result_extraction_postprocess_validation.schema.json"),
        Path(
            "configs/comsol/result_extraction_postprocess_validation/static_contract.yaml"
        ),
    ),
]

RUNTIME_CASES = [
    (
        Path("schemas/comsol_C03_geometry_mesh_import_contract.schema.json"),
        Path(
            "configs/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle.yaml"
        ),
    ),
    (
        Path("schemas/comsol_C04_physics_boundary_assignment_contract.schema.json"),
        Path(
            "configs/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle.yaml"
        ),
    ),
    (
        Path("schemas/comsol_C05_study_run_solver_smoke.schema.json"),
        Path(
            "configs/comsol/study_run_solver_smoke/local_livelink_heat_rectangle.yaml"
        ),
    ),
    (
        Path("schemas/comsol_C06_result_extraction_postprocess_validation.schema.json"),
        Path(
            "configs/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle.yaml"
        ),
    ),
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_comsol_c03_c06_static_configs_match_schema() -> None:
    failures = {}
    for schema_path, config_path in CASES:
        errors = sorted(
            Draft202012Validator(_read_json(schema_path)).iter_errors(
                _read_yaml(config_path)
            ),
            key=lambda error: list(error.path),
        )
        if errors:
            failures[config_path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_comsol_c03_c06_runtime_configs_match_schema() -> None:
    failures = {}
    for schema_path, config_path in RUNTIME_CASES:
        errors = sorted(
            Draft202012Validator(_read_json(schema_path)).iter_errors(
                _read_yaml(config_path)
            ),
            key=lambda error: list(error.path),
        )
        if errors:
            failures[config_path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_comsol_c03_c06_static_schemas_reject_unknown_key() -> None:
    for schema_path, config_path in CASES:
        config = copy.deepcopy(_read_yaml(config_path))
        config["hidden_local_comsol_path"] = "local-path-should-not-be-accepted"

        errors = list(Draft202012Validator(_read_json(schema_path)).iter_errors(config))

        assert errors, config_path
        assert any("Additional properties" in error.message for error in errors)
