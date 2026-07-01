from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/gmsh_C02_boundary_physical_group_contract.schema.json")
CONFIG_PATH = Path("configs/gmsh/boundary_physical_group_contract/baseline.yaml")
CONFIG_DIR = CONFIG_PATH.parent


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_gmsh_c02_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_gmsh_c02_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_gmsh_c02_schema_rejects_unknown_key() -> None:
    config = copy.deepcopy(_config())
    config["hidden_solver_guess"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_gmsh_c02_config_declares_required_boundary_contract() -> None:
    config = _config()
    groups = {item["name"]: item for item in config["physical_groups"]}

    assert {"inlet", "outlet", "wall", "fluid_domain"}.issubset(groups)
    assert groups["fluid_domain"]["dimension"] == 2
    assert groups["fluid_domain"]["role"] == "domain"
    assert config["downstream_boundary_map"]["target_solver"] == "openfoam"
    assert set(config["downstream_boundary_map"]["required_roles"]) == {"inlet", "outlet", "wall", "domain"}
