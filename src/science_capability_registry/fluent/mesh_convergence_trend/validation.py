"""Validation helpers for Fluent C03 mesh convergence trends."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_strictly_increasing(values: list[int]) -> bool:
    return all(next_value > value for value, next_value in zip(values, values[1:]))


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    cell_counts = [level["nominal_cell_count"] for level in manifest["mesh_levels"]]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "mesh_level_count": len(manifest["mesh_levels"]),
        "monitored_quantity_count": len(manifest["monitored_quantities"]),
        "failure_class_count": len(manifest["failure_classification"]),
        "cell_counts": cell_counts,
        "cell_count_ratio_last_first": cell_counts[-1] / cell_counts[0] if cell_counts else None,
        "cell_counts_strictly_increasing": _is_strictly_increasing(cell_counts),
        "runtime_status": "not_executed_in_static_trend_contract",
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cell_counts = [level["nominal_cell_count"] for level in manifest["mesh_levels"]]
    source_roles = {source["source_role"] for source in manifest["source_basis"]}
    quantity_ids = {quantity["quantity_id"] for quantity in manifest["monitored_quantities"]}
    failure_classes = {item["failure_class"] for item in manifest["failure_classification"]}

    _check(
        checks,
        "trend.min_mesh_levels",
        len(manifest["mesh_levels"]) >= config["validation"]["min_mesh_levels"],
        str(len(manifest["mesh_levels"])),
    )
    _check(
        checks,
        "trend.cell_counts_strictly_increasing",
        _is_strictly_increasing(cell_counts),
        json.dumps(cell_counts),
    )
    for required_role in config["validation"]["required_source_roles"]:
        _check(checks, f"source.role.{required_role}", required_role in source_roles, json.dumps(sorted(source_roles)))
    for required_quantity in config["validation"]["required_monitored_quantities"]:
        _check(
            checks,
            f"quantity.{required_quantity}",
            required_quantity in quantity_ids,
            json.dumps(sorted(quantity_ids)),
        )
    for required_class in config["validation"]["required_failure_classes"]:
        _check(
            checks,
            f"failure_class.{required_class}",
            required_class in failure_classes,
            json.dumps(sorted(failure_classes)),
        )

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            _check(checks, f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C03 mesh convergence static trend contract; no Fluent solver execution",
        "checks": checks,
        "details": {
            "cell_counts": cell_counts,
            "quantity_ids": sorted(quantity_ids),
            "no_claims": config["validation"]["no_claims"],
        },
    }

