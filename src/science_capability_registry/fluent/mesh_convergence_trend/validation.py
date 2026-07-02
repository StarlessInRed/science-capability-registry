"""Validation helpers for Fluent C03 mesh convergence trends."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_strictly_increasing(values: list[int]) -> bool:
    return all(next_value > value for value, next_value in zip(values, values[1:]))


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and value == value


def _adjacent_relative_changes(values: list[float]) -> list[float]:
    changes = []
    for previous, current in zip(values, values[1:]):
        denominator = abs(previous) if abs(previous) > 0.0 else 1.0
        changes.append(abs(current - previous) / denominator)
    return changes


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


def summarize_runtime_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    result = summarize_metrics(manifest, validation)
    runtime_levels = manifest["runtime_levels"]
    pressure_drops = [level.get("runtime_pressure_drop_pa") for level in runtime_levels]
    numeric_pressure_drops = [float(value) for value in pressure_drops if _is_number(value)]
    adjacent_changes = _adjacent_relative_changes(numeric_pressure_drops)
    result.update(
        {
            "runtime_status": "executed_c02_pressure_drop_refinement_smoke",
            "level_validation_passed": [bool(level.get("validation_passed")) for level in runtime_levels],
            "pressure_drops_pa": pressure_drops,
            "pressure_drop_relative_errors": [level.get("pressure_drop_relative_error") for level in runtime_levels],
            "adjacent_pressure_drop_relative_changes": adjacent_changes,
            "max_adjacent_pressure_drop_relative_change": max(adjacent_changes) if adjacent_changes else None,
        }
    )
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


def validate_runtime_manifest(
    manifest: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    validation = validate_manifest(manifest, config, output_dir)
    checks = list(validation["checks"])
    runtime_levels = manifest["runtime_levels"]
    pressure_drops = [level.get("runtime_pressure_drop_pa") for level in runtime_levels]
    numeric_pressure_drops = [float(value) for value in pressure_drops if _is_number(value)]
    adjacent_changes = _adjacent_relative_changes(numeric_pressure_drops)

    for level in runtime_levels:
        level_id = level["level_id"]
        _check(
            checks,
            f"runtime.level.{level_id}.validation_passed",
            bool(level.get("validation_passed")),
            str(level.get("validation_passed")),
        )
        _check(
            checks,
            f"runtime.level.{level_id}.pressure_drop_present",
            _is_number(level.get("runtime_pressure_drop_pa")),
            str(level.get("runtime_pressure_drop_pa")),
        )
        _check(
            checks,
            f"runtime.level.{level_id}.pressure_error_bound",
            _is_number(level.get("pressure_drop_relative_error"))
            and float(level["pressure_drop_relative_error"]) <= config["validation"]["max_pressure_drop_relative_error"],
            f"{level.get('pressure_drop_relative_error')} <= {config['validation']['max_pressure_drop_relative_error']}",
        )
    _check(
        checks,
        "runtime.all_level_validations_pass",
        (not config["validation"]["require_all_level_validations_pass"])
        or all(bool(level.get("validation_passed")) for level in runtime_levels),
        json.dumps([bool(level.get("validation_passed")) for level in runtime_levels]),
    )
    _check(
        checks,
        "runtime.pressure_drop_count",
        len(numeric_pressure_drops) == len(runtime_levels),
        json.dumps(pressure_drops),
    )
    max_change = max(adjacent_changes) if adjacent_changes else None
    _check(
        checks,
        "runtime.adjacent_pressure_drop_change_bound",
        max_change is not None and max_change <= config["validation"]["max_adjacent_pressure_drop_change"],
        f"{max_change} <= {config['validation']['max_adjacent_pressure_drop_change']}",
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": (
            "Fluent C03 runtime mesh-refinement smoke using C02 pressure-drop solves; "
            "uniform-inlet analytical homology remains unclaimed"
        ),
        "checks": checks,
        "details": {
            "pressure_drops_pa": pressure_drops,
            "adjacent_pressure_drop_relative_changes": adjacent_changes,
            "no_claims": config["validation"]["no_claims"],
        },
    }
