from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def _load_schema() -> dict:
    return json.loads(Path("schemas/fluent_C04_external_aero_force_coefficients.schema.json").read_text(encoding="utf-8"))


def _load_config() -> dict:
    return yaml.safe_load(
        Path("configs/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_fluent_c04_reference_config_matches_schema() -> None:
    schema = _load_schema()
    config = _load_config()

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["backend"]["type"] == "reference_csv_parser"
    assert config["validation"]["gate"] == "static-readiness"


def test_fluent_c04_schema_rejects_unknown_key() -> None:
    schema = _load_schema()
    config = _load_config()
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors


def test_fluent_c04_schema_requires_no_claims() -> None:
    schema = _load_schema()
    config = _load_config()
    config["validation"].pop("no_claims")

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert any("no_claims" in error.message for error in errors)
