from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "cantera" / "c03_counterflow_diffusion_flame"
SCHEMA_PATH = ROOT / "schemas" / "cantera_C03_counterflow_diffusion_flame.schema.json"


def test_all_c03_configs_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    config_paths = sorted(CONFIG_DIR.glob("*.yaml"))
    assert config_paths

    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: error.path)
        assert not errors, f"{config_path.name}: {[error.message for error in errors]}"


def test_baseline_exposes_required_modes() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    modes = {mode["mode"]: mode for mode in config["radiation_modes"]}
    assert modes["no_radiation"]["enabled"] is False
    assert modes["radiation"]["enabled"] is True

