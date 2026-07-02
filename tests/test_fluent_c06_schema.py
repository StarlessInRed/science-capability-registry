from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c06_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C06_sliding_rotating_mesh.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["validation"]["min_mesh_entries"] == 2


def test_fluent_c06_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C06_sliding_rotating_mesh.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors
