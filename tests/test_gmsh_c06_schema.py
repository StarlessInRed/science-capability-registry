from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/gmsh_C06_multi_solver_mesh_export_contract.schema.json")
CONFIG_PATH = Path("configs/gmsh/multi_solver_mesh_export_contract/baseline.yaml")
CONFIG_DIR = CONFIG_PATH.parent


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_gmsh_c06_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_gmsh_c06_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_gmsh_c06_schema_rejects_unknown_key() -> None:
    config = copy.deepcopy(_config())
    config["hidden_import_guess"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_gmsh_c06_config_declares_two_solver_families() -> None:
    config = _config()
    targets = {item["target_id"]: item for item in config["export_targets"]}

    assert set(targets) == {"openfoam_gmshToFoam", "fenicsx_xdmf"}
    assert {item["solver_family"] for item in targets.values()} == {"cfd", "fem"}
    assert config["source_mesh"]["boundary_contract_id"] == "meshing.gmsh.boundary_physical_group_contract"
    assert config["source_mesh"]["quality_contract_id"] == "meshing.gmsh.mesh_refinement_quality_trend"
