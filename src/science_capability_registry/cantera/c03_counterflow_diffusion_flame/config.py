"""Configuration loading and schema validation for Cantera C03."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "schemas" / "cantera_C03_counterflow_diffusion_flame.schema.json"


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping from disk."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {config_path}")
    data["_config_path"] = str(config_path)
    return data


def load_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    """Load the JSON schema used by C03 run configs."""
    path = Path(schema_path) if schema_path is not None else SCHEMA_PATH
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_case_config(
    config: dict[str, Any], schema_path: str | Path | None = None
) -> dict[str, Any]:
    """Validate a C03 run config and return it unchanged on success."""
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    public_config = {key: value for key, value in config.items() if not key.startswith("_")}
    errors = sorted(validator.iter_errors(public_config), key=lambda error: error.path)
    if errors:
        messages = []
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{path}: {error.message}")
        raise ValueError("Invalid Cantera C03 config:\n" + "\n".join(messages))
    return config


def load_case_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a C03 run config."""
    return validate_case_config(load_yaml(path))


def repo_relative_path(path_value: str | Path) -> Path:
    """Resolve a repo-relative path while allowing absolute paths."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path

