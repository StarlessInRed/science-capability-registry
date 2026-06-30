"""Configuration loading for OpenFOAM C04."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.config_contract import (
    REPO_ROOT,
    load_json_schema,
    load_yaml_mapping,
    repo_relative_path,
    validate_mapping,
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "openfoam_C04_external_aero_motorbike_rans_snappy.schema.json"


def load_yaml(path: str | Path) -> dict[str, Any]:
    return load_yaml_mapping(path)


def load_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path is not None else SCHEMA_PATH
    return load_json_schema(path)


def validate_case_config(config: dict[str, Any], schema_path: str | Path | None = None) -> dict[str, Any]:
    return validate_mapping(config, load_schema(schema_path), "OpenFOAM C04")


def load_case_config(path: str | Path) -> dict[str, Any]:
    return validate_case_config(load_yaml(path))
