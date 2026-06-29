from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "cantera" / "c02_freely_propagating_premixed_flame"
SCHEMA_PATH = ROOT / "schemas" / "cantera_C02_freely_propagating_premixed_flame.schema.json"


def test_c02_configs_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    config_paths = sorted(CONFIG_DIR.glob("*.yaml"))
    assert config_paths

    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: error.path)
        assert not errors, f"{config_path.name}: {[error.message for error in errors]}"


def test_c02_baseline_matches_official_transport_sequence() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    assert [mode["mode"] for mode in config["transport_modes"]] == [
        "mixture_averaged",
        "mixture_averaged_soret",
        "multicomponent",
        "multicomponent_soret",
    ]
    assert config["transport_modes"][0]["flux_gradient_basis"] == "mass"
