"""Load and validate the cross-software capability catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = REPO_ROOT / "configs" / "registry" / "capability_catalog.json"
CATALOG_SCHEMA_PATH = REPO_ROOT / "schemas" / "capability_registry.schema.json"
EVIDENCE_INDEX_PATH = REPO_ROOT / "reports" / "evidence_index.yaml"


def load_json_mapping(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON mapping in {resolved}")
    return data


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {resolved}")
    return data


def validate_mapping(data: dict[str, Any], schema_path: str | Path, label: str) -> dict[str, Any]:
    schema = load_json_mapping(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    if errors:
        messages = []
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{path}: {error.message}")
        raise ValueError(f"Invalid {label}:\n" + "\n".join(messages))
    return data


def load_catalog(path: str | Path = CATALOG_PATH) -> dict[str, Any]:
    return validate_mapping(load_json_mapping(path), CATALOG_SCHEMA_PATH, "capability catalog")


def load_evidence_index(path: str | Path = EVIDENCE_INDEX_PATH) -> dict[str, Any]:
    return load_yaml_mapping(path)


def catalog_entries_by_id(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    source = load_catalog() if catalog is None else catalog
    entries: dict[str, dict[str, Any]] = {}
    for entry in source["capabilities"]:
        capability_id = str(entry["capability_id"])
        if capability_id in entries:
            raise ValueError(f"Duplicate capability_id in catalog: {capability_id}")
        entries[capability_id] = entry
    return entries


def evidence_entries_by_id(evidence_index: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    source = load_evidence_index() if evidence_index is None else evidence_index
    entries: dict[str, dict[str, Any]] = {}
    for entry in source.get("evidence", []):
        evidence_id = str(entry["evidence_id"])
        if evidence_id in entries:
            raise ValueError(f"Duplicate evidence_id in index: {evidence_id}")
        entries[evidence_id] = entry
    return entries


def resolve_capability(capability_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    entries = catalog_entries_by_id(catalog)
    if capability_id not in entries:
        raise ValueError(f"Unknown capability_id: {capability_id}")
    return entries[capability_id]


def repo_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path
