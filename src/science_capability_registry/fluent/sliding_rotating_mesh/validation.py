"""Validation helpers for Fluent C06 sliding/rotating mesh setup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    mesh_entries = manifest["mesh_entries"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "source_package_count": len(manifest["packages"]),
        "readable_package_count": sum(1 for package in manifest["packages"] if package["archive_status"] == "readable"),
        "mesh_entry_count": len(mesh_entries),
        "mesh_format_counts": manifest["mesh_format_counts"],
        "total_mesh_bytes": sum(int(entry["size"]) for entry in mesh_entries),
        "moving_zone_runtime_status": "not_extracted_in_setup_manifest",
        "solver_replay_status": "not_available_from_mesh_only_sources",
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    metrics = summarize_metrics(manifest)
    expected_ids = set(config["validation"]["required_source_ids"])
    present_ids = {package["source_id"] for package in manifest["packages"]}

    _check(checks, "sources.required_source_ids", expected_ids == present_ids, str(sorted(present_ids)))
    _check(
        checks,
        "sources.readable",
        metrics["readable_package_count"] == metrics["source_package_count"],
        f"{metrics['readable_package_count']} / {metrics['source_package_count']}",
    )
    for package in manifest["packages"]:
        kind_counts = package["entry_kind_counts"]
        _check(
            checks,
            f"source.{package['source_id']}.mesh_present",
            kind_counts.get("mesh", 0) > 0,
            json.dumps(kind_counts, sort_keys=True),
        )
        _check(
            checks,
            f"source.{package['source_id']}.mesh_only_boundary",
            kind_counts.get("case", 0) == 0 and kind_counts.get("data", 0) == 0,
            json.dumps(kind_counts, sort_keys=True),
        )
    _check(checks, "source.mesh_entry_count", metrics["mesh_entry_count"] >= config["validation"]["min_mesh_entries"], str(metrics["mesh_entry_count"]))

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
        "scope": "Fluent C06 sliding/rotating mesh source manifest; no moving-zone or sliding-mesh solver execution",
        "checks": checks,
        "details": {
            "mesh_entries": [entry["entry_path"] for entry in manifest["mesh_entries"]],
            "no_claims": config["validation"]["no_claims"],
        },
    }
