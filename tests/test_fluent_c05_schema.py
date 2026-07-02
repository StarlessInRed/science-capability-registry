from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c05_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C05_vof_free_surface_transient.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["validation"]["min_mesh_entries"] == 1


def test_fluent_c05_runtime_smoke_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C05_vof_free_surface_transient.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_read_smoke.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert config["backend"]["type"] == "fluent_mesh_read_smoke"


def test_fluent_c05_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C05_vof_free_surface_transient.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors
