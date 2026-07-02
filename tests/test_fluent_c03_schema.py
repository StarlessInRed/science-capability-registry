from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_c03_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_C03_mesh_convergence_trend.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml").read_text(
            encoding="utf-8"
        )
    )

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)

    assert errors == []
    assert config["backend"]["type"] == "mesh_trend_static"
    assert len(config["mesh_levels"]) == 3


def test_fluent_c03_schema_rejects_unknown_key() -> None:
    schema = json.loads(Path("schemas/fluent_C03_mesh_convergence_trend.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(
        Path("configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["legacy_status"] = "do_not_allow"

    errors = list(Draft202012Validator(schema).iter_errors(config))

    assert errors

