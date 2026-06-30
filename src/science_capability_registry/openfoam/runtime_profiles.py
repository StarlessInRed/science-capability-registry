"""Runtime profile loading for OpenFOAM host integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.config_contract import (
    REPO_ROOT,
    load_json_schema,
    load_yaml_mapping,
    validate_mapping,
)

PROFILE_SCHEMA_PATH = REPO_ROOT / "schemas" / "openfoam_runtime_profile.schema.json"
PROFILE_DIR = REPO_ROOT / "configs" / "openfoam" / "runtime_profiles"


def load_runtime_profile_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path is not None else PROFILE_SCHEMA_PATH
    return load_json_schema(path)


def validate_runtime_profile(
    profile: dict[str, Any],
    schema_path: str | Path | None = None,
) -> dict[str, Any]:
    return validate_mapping(profile, load_runtime_profile_schema(schema_path), "OpenFOAM runtime profile")


def load_runtime_profile(path: str | Path) -> dict[str, Any]:
    return validate_runtime_profile(load_yaml_mapping(path))


def profile_path(profile_id: str) -> Path:
    if not profile_id:
        raise ValueError("profile_id must not be empty")
    return PROFILE_DIR / f"{profile_id}.yaml"
