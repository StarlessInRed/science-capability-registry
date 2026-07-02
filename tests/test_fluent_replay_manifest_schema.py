from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def test_fluent_replay_manifest_config_matches_schema() -> None:
    schema = json.loads(Path("schemas/fluent_official_replay_manifest.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(Path("configs/fluent/official_replay_manifest/c01_c08_sources.yaml").read_text(encoding="utf-8"))

    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda error: error.path)
    assert errors == []
    assert [binding["seed_id"] for binding in config["capability_bindings"]] == [
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
        "C06",
        "C07",
        "C08",
    ]


def test_fluent_replay_manifest_schema_rejects_non_relative_path() -> None:
    schema = json.loads(Path("schemas/fluent_official_replay_manifest.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(Path("configs/fluent/official_replay_manifest/c01_c08_sources.yaml").read_text(encoding="utf-8"))
    config["source_packages"][0]["rel_path"] = "/absolute/source.zip"

    errors = list(Draft202012Validator(schema).iter_errors(config))
    assert errors
