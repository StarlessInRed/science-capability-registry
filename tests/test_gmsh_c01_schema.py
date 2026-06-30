from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/gmsh_C01_parametric_geometry_mesh_generation.schema.json")
CONFIG_PATH = Path("configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_gmsh_c01_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_gmsh_c01_schema_rejects_unknown_key() -> None:
    config = _config()
    config["hidden_choice"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_gmsh_c01_config_declares_required_physical_groups() -> None:
    config = _config()
    groups = {item["name"] for item in config["physical_groups"]}

    assert {"inlet", "outlet", "wall", "fluid_domain"}.issubset(groups)
    assert config["mesh"]["dimension"] == 2
    assert config["mesh"]["element_order"] == 1
