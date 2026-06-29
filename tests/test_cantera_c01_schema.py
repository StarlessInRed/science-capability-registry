from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "cantera" / "c01_constant_pressure_ignition"
SCHEMA_PATH = ROOT / "schemas" / "cantera_C01_constant_pressure_ignition.schema.json"


def test_c01_configs_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    config_paths = sorted(CONFIG_DIR.glob("*.yaml"))
    assert config_paths

    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: error.path)
        assert not errors, f"{config_path.name}: {[error.message for error in errors]}"


def test_c01_baseline_matches_official_reactor_setup() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    assert config["mechanism"] == "h2o2.yaml"
    assert config["reactor_model"] == "ideal_gas_constant_pressure"
    assert config["initial_temperature_k"] == 1001.0
    assert config["pressure_pa"] == 101325.0
    assert config["composition"] == "H2:2,O2:1,N2:4"
    assert config["advance"]["dt_max_s"] == 1.0e-5
    assert config["advance"]["t_end_s"] == 1.0e-3
