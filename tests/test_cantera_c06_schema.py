from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "cantera" / "c06_mechanism_reduction"
SCHEMA_PATH = ROOT / "schemas" / "cantera_C06_mechanism_reduction.schema.json"


def test_c06_configs_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    config_paths = sorted(CONFIG_DIR.glob("*.yaml"))
    assert config_paths

    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: error.path)
        assert not errors, f"{config_path.name}: {[error.message for error in errors]}"


def test_c06_baseline_matches_official_reduction_setup() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    assert config["mechanism"] == "example_data/n-hexane-NUIG-2015.yaml"
    assert config["reactor_model"] == "ideal_gas_constant_pressure_mole"
    assert config["initial_temperature_k"] == 975.0
    assert config["pressure_pa"] == 506625.0
    assert config["equivalence_ratio"] == 0.8
    assert config["fuel"] == "NC6H14:1.0"
    assert config["oxidizer"] == "O2:1.0, N2:3.76"
    assert config["simulation"]["end_time_s"] == 0.04
    assert config["reduction"]["reaction_counts"] == [100, 200, 300, 400, 600, 800]
