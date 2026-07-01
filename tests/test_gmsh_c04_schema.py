from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/gmsh_C04_cad_import_geometry_healing.schema.json")
CONFIG_PATH = Path("configs/gmsh/cad_import_geometry_healing/baseline.yaml")
CONFIG_DIR = CONFIG_PATH.parent


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_gmsh_c04_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_gmsh_c04_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_gmsh_c04_schema_rejects_unknown_key() -> None:
    config = copy.deepcopy(_config())
    config["hidden_cad_file_path"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_gmsh_c04_config_declares_generated_smoke_without_large_cad() -> None:
    config = _config()

    assert config["cad_source"]["source_kind"] == "generated_smoke"
    assert config["cad_source"]["source_ref"].startswith("generated://")
    assert {item["operation"] for item in config["healing_operations"]} == {"sew_faces", "remove_duplicates"}
