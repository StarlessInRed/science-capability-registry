from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/fluent_C01_steady_internal_flow_runtime.schema.json")
CONFIG_PATH = Path("configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml")
CONFIG_DIR = CONFIG_PATH.parent


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_fluent_c01_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_fluent_c01_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_fluent_c01_schema_rejects_unknown_key() -> None:
    config = copy.deepcopy(_config())
    config["hidden_solver_path"] = "local-path-should-not-be-accepted"

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_fluent_c01_config_uses_environment_boundary() -> None:
    config = _config()

    assert config["fluent"]["executable_env"] == "FLUENT_EXE"
    assert config["source_case"]["source_root_env"] == "FLUENT_TUTORIAL_ROOT"
    strings: list[str] = []

    def collect_strings(value: Any) -> None:
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                collect_strings(item)
        elif isinstance(value, list):
            for item in value:
                collect_strings(item)

    collect_strings(config)
    assert not any(":\\" in value or ":/" in value for value in strings)
