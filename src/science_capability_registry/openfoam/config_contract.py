"""Shared config loading and schema validation for OpenFOAM capabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {config_path}")
    data["_config_path"] = str(config_path)
    return data


def load_json_schema(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict):
        raise ValueError(f"Expected a JSON schema object in {path}")
    return schema


def validate_mapping(
    config: dict[str, Any],
    schema: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    private_keys = [key for key in config if key.startswith("_") and key != "_config_path"]
    if private_keys:
        joined = ", ".join(sorted(private_keys))
        raise ValueError(f"Invalid {label} config private keys: {joined}")

    public_config = {key: value for key, value in config.items() if key != "_config_path"}
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(public_config), key=lambda error: error.path)
    if errors:
        messages = []
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{path}: {error.message}")
        raise ValueError(f"Invalid {label} config:\n" + "\n".join(messages))
    return config


def repo_relative_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path
