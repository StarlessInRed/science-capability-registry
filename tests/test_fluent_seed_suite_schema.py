from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/fluent_seed_suite.schema.json")
CONFIG_PATH = Path("configs/fluent/seed_suite/c01_c08_static_readiness.yaml")
CONFIG_DIR = CONFIG_PATH.parent


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_fluent_seed_suite_baseline_config_matches_schema() -> None:
    errors = sorted(Draft202012Validator(_schema()).iter_errors(_config()), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]


def test_fluent_seed_suite_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_fluent_seed_suite_schema_rejects_unknown_key() -> None:
    config = copy.deepcopy(_config())
    config["hidden_local_fluent_path"] = "local-path-should-not-be-accepted"

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_fluent_seed_suite_declares_exact_c01_c08_seed_set() -> None:
    config = _config()
    seed_ids = [seed["seed_id"] for seed in config["seed_cases"]]
    statuses = {seed["seed_id"]: seed["benchmark_status"] for seed in config["seed_cases"]}

    assert seed_ids == ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"]
    assert statuses["C01"] == "package_skeleton_created"
    assert statuses["C02"] == "package_skeleton_created"
    assert statuses["C03"] == "package_skeleton_created"
    assert all(statuses[seed_id] == "benchmark_candidate" for seed_id in seed_ids[3:])
    assert set(config["learning_loop"]["required_modes"]) == {"self_generated", "official_replay", "comparison"}
