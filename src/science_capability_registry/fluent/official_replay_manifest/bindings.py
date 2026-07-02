"""Capability binding validation for Fluent replay manifests."""

from __future__ import annotations

from typing import Any


def source_ids_by_seed(config: dict[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for source in config["source_packages"]:
        result.setdefault(source["seed_id"], set()).add(source["source_id"])
    return result


def binding_errors(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    all_source_ids = {source["source_id"] for source in config["source_packages"]}
    seen_seed_ids = set()
    for binding in config["capability_bindings"]:
        seed_id = binding["seed_id"]
        if seed_id in seen_seed_ids:
            errors.append(f"duplicate binding for {seed_id}")
        seen_seed_ids.add(seed_id)
        for source_id in binding["source_ids"]:
            if source_id not in all_source_ids:
                errors.append(f"{seed_id} references unknown source_id {source_id}")
    required = set(config["validation"]["required_seed_ids"])
    missing = sorted(required - seen_seed_ids)
    if missing:
        errors.append(f"missing bindings for {missing}")
    return errors


def bindings_with_source_summaries(config: dict[str, Any], package_summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for binding in config["capability_bindings"]:
        source_summaries = [package_summaries[source_id] for source_id in binding["source_ids"] if source_id in package_summaries]
        result.append({**binding, "source_summaries": source_summaries})
    return result
