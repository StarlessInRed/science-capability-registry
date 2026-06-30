from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.config import validate_case_config

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "openfoam" / "lid_driven_cavity_incompressible_laminar"
SCHEMA_PATH = ROOT / "schemas" / "openfoam_C01_lid_driven_cavity_incompressible_laminar.schema.json"


def test_openfoam_c01_configs_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    config_paths = sorted(CONFIG_DIR.glob("*.yaml"))
    assert config_paths

    for config_path in config_paths:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: error.path)
        assert not errors, f"{config_path.name}: {[error.message for error in errors]}"


def test_openfoam_c01_baseline_matches_official_cavity_setup() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    assert config["solver"]["name"] == "icoFoam"
    assert config["mesh"]["cells"] == [20, 20, 1]
    assert config["geometry"]["cavity_side_length_m"] == 0.1
    assert config["material"]["kinematic_viscosity_m2_s"] == 0.01
    assert config["material"]["reynolds_number"] == 10
    assert config["fields"]["U"]["boundaries"]["movingWall"]["value"] == "uniform (1 0 0)"
    assert config["fields"]["U"]["boundaries"]["frontAndBack"]["type"] == "empty"
    assert config["numerics"]["control"]["end_time_s"] == 0.5
    assert config["numerics"]["control"]["delta_t_s"] == 0.005


def test_openfoam_c01_runtime_config_rejects_unknown_private_keys() -> None:
    config = yaml.safe_load((CONFIG_DIR / "baseline.yaml").read_text(encoding="utf-8"))
    config["_unexpected"] = "bad"

    with pytest.raises(ValueError, match="_unexpected"):
        validate_case_config(config)

