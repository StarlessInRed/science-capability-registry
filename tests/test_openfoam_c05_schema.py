from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator


SCHEMA_PATH = Path("schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json")
CONFIG_PATH = Path("configs/openfoam/transient_cylinder_vortex_shedding/baseline_cylinder2d.yaml")
CONFIG_DIR = CONFIG_PATH.parent
ASSET_PATH = Path("software/openfoam/assets/C05_transient_cylinder_vortex_shedding.yaml")
TASK_PATH = Path("tasks/openfoam_C05_transient_cylinder_vortex_shedding_intern_task.md")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_openfoam_c05_baseline_config_matches_schema() -> None:
    validator = Draft202012Validator(_schema())
    errors = sorted(validator.iter_errors(_config()), key=lambda error: list(error.path))
    assert not errors, [error.message for error in errors]


def test_openfoam_c05_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_openfoam_c05_schema_accepts_v2412_native_forcecoeffs_smoke() -> None:
    config = yaml.safe_load(
        (CONFIG_DIR / "runtime_forcecoeffs_smoke_wsl_v2412.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(_schema()).iter_errors(config), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]
    assert config["openfoam"]["runtime_profile"] == "openfoam_com_v2412"
    assert config["postprocess"]["force_extraction_source"] == "openfoam_forceCoeffs"
    assert config["postprocess"]["strouhal_estimate"] is False


def test_openfoam_c05_schema_rejects_untracked_top_level_key() -> None:
    config = _config()
    config["hidden_choice"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_openfoam_c05_assets_record_validation_failure() -> None:
    asset = yaml.safe_load(ASSET_PATH.read_text(encoding="utf-8"))
    task_text = TASK_PATH.read_text(encoding="utf-8")

    assert asset["integration_targets"]["input_schema"] == SCHEMA_PATH.as_posix()
    assert asset["benchmark_status"] == "validation_failed"
    assert "validation_failed" in task_text


def test_openfoam_c05_schema_rejects_wrong_solver() -> None:
    config = _config()
    config["solver"]["name"] = "simpleFoam"

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("pimpleFoam" in error.message for error in errors)
