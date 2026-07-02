from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c07_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C07_heat_transfer_energy_balance.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_static.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["validation"]["min_case_data_pairs"] == 1


def test_fluent_c07_runtime_smoke_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C07_heat_transfer_energy_balance.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_read_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["backend"]["type"] == "fluent_case_data_read_smoke"
    assert config["runtime_smoke"]["thermal_reports"]["temperature_surfaces"] == ["inlet", "outlet"]


def test_fluent_c07_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C07_heat_transfer_energy_balance.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors
