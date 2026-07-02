"""Validation helpers for Fluent C08 Workbench parameter integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    nested_counts = manifest["nested_archive"]["entry_kind_counts"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "outer_archive_status": manifest["outer_archive"]["archive_status"],
        "nested_archive_status": manifest["nested_archive"]["archive_status"],
        "nested_entry_count": manifest["nested_archive"]["entry_count"],
        "current_parameter_count": len(manifest["current_parameters"]),
        "historical_design_point_row_count": manifest["design_point_log"]["data_row_count"],
        "workbench_project_version": manifest["workbench_project"]["external_version_string"],
        "workbench_build_version": manifest["workbench_project"]["framework_build_version"],
        "workbench_journal_count": nested_counts.get("workbench_journal", 0),
        "geometry_database_count": nested_counts.get("geometry_database", 0),
        "mesh_database_count": nested_counts.get("mesh_database", 0),
        "runwb2_env_configured": manifest["runwb2_preflight"]["runwb2_executable"]["configured"],
        "workbench_runtime_status": "not_executed_in_static_preflight",
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    nested_counts = manifest["nested_archive"]["entry_kind_counts"]

    _check(checks, "outer_archive.readable", manifest["outer_archive"]["archive_status"] == "readable", manifest["outer_archive"]["error_message"])
    _check(checks, "nested_archive.readable", manifest["nested_archive"]["archive_status"] == "readable", manifest["nested_archive"]["error_message"])
    for required_kind in config["validation"]["required_nested_entry_classes"]:
        _check(
            checks,
            f"nested.entry_class.{required_kind}",
            nested_counts.get(required_kind, 0) > 0,
            json.dumps(nested_counts, sort_keys=True),
        )
    _check(
        checks,
        "project.current_parameter_count",
        len(manifest["current_parameters"]) >= config["validation"]["min_current_parameters"],
        str(len(manifest["current_parameters"])),
    )
    _check(
        checks,
        "project.external_version_detected",
        bool(manifest["workbench_project"]["external_version_string"]),
        manifest["workbench_project"]["external_version_string"],
    )
    _check(
        checks,
        "preflight.runwb2_not_required_for_static_gate",
        manifest["runwb2_preflight"]["static_gate_requires_runwb2"] is False,
        json.dumps(manifest["runwb2_preflight"], sort_keys=True),
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
        "scope": "Fluent C08 Workbench WBPZ static preflight; no RunWB2 execution or project migration",
        "checks": checks,
        "details": {
            "current_parameter_names": [parameter["parameter_name"] for parameter in manifest["current_parameters"]],
            "no_claims": config["validation"]["no_claims"],
        },
    }
