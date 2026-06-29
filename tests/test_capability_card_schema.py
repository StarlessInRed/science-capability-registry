from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "capability_card.schema.json"
ASSET_DIR = ROOT / "software"


def test_capability_cards_match_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    asset_paths = sorted(ASSET_DIR.glob("*/assets/*.yaml"))
    assert asset_paths

    for asset_path in asset_paths:
        asset = yaml.safe_load(asset_path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(asset), key=lambda error: error.path)
        assert not errors, f"{asset_path.relative_to(ROOT)}: {[error.message for error in errors]}"
