"""Validation helpers for Fluent C05 VOF source setup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    entries = manifest["mesh_entries"]
    archive = manifest["archive"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "archive_status": archive["archive_status"],
        "archive_entry_count": archive["entry_count"],
        "mesh_entry_count": len(entries),
        "mesh_format_counts": manifest["mesh_format_counts"],
        "total_mesh_bytes": sum(int(entry["size"]) for entry in entries),
        "solver_replay_status": "not_available_from_mesh_only_source",
        "vof_runtime_status": "not_extracted_in_setup_manifest",
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    archive = manifest["archive"]

    _check(checks, "archive.readable", archive["archive_status"] == "readable", archive["error_message"])
    for required_kind in config["validation"]["required_entry_classes"]:
        _check(
            checks,
            f"archive.entry_class.{required_kind}",
            archive["entry_kind_counts"].get(required_kind, 0) > 0,
            json.dumps(archive["entry_kind_counts"], sort_keys=True),
        )
    _check(
        checks,
        "source.mesh_entry_count",
        len(manifest["mesh_entries"]) >= config["validation"]["min_mesh_entries"],
        str(len(manifest["mesh_entries"])),
    )
    _check(
        checks,
        "source.mesh_only_boundary",
        archive["entry_kind_counts"].get("case", 0) == 0 and archive["entry_kind_counts"].get("data", 0) == 0,
        json.dumps(archive["entry_kind_counts"], sort_keys=True),
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
        "scope": "Fluent C05 VOF mesh/setup source manifest; no transient VOF solver execution",
        "checks": checks,
        "details": {
            "mesh_entries": [entry["entry_path"] for entry in manifest["mesh_entries"]],
            "no_claims": config["validation"]["no_claims"],
        },
    }
