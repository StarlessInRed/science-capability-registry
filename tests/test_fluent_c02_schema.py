from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c02_reference_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C02_verification_reference_validation.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["reference_source"]["manual_case_id"] == "VMFL005"
    assert config["reference_formula"]["formula_id"] == "hagen_poiseuille_pressure_drop"


def test_fluent_c02_mesh_smoke_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C02_verification_reference_validation.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["backend"]["type"] == "fluent_mesh_check"
    assert config["mesh_generation"]["zone_names"]["axis"] == "axis"


def test_fluent_c02_pressure_solve_smoke_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C02_verification_reference_validation.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path(
            "configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_pressure_solve_smoke.yaml"
        ).read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["backend"]["type"] == "fluent_pressure_solve_smoke"
    assert config["solver_setup"]["pressure_report_status"] == "report_command_not_closed"


def test_fluent_c02_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C02_verification_reference_validation.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors


def test_fluent_c02_schema_requires_sampling_policy() -> None:
    schema = json.loads(Path("schemas/fluent_C02_verification_reference_validation.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml").read_text(
            encoding="utf-8"
        )
    )
    config.pop("sampling_policy")

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert any("sampling_policy" in error.message for error in errors)
