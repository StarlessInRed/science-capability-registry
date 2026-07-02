from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c08_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C08_workbench_parameter_integration.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["validation"]["min_current_parameters"] == 3


def test_fluent_c08_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C08_workbench_parameter_integration.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors
