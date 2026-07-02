"""Validation helpers for Fluent C07 heat-transfer source readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    entries = manifest["entries"]
    archive = manifest["archive"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "archive_status": archive["archive_status"],
        "archive_entry_count": archive["entry_count"],
        "case_entry_count": archive["entry_kind_counts"].get("case", 0),
        "data_entry_count": archive["entry_kind_counts"].get("data", 0),
        "case_data_pair_count": len(manifest["case_data_pairs"]),
        "total_uncompressed_bytes": sum(int(entry["size"]) for entry in entries),
        "heat_rate_runtime_status": "not_extracted_in_source_manifest",
        "temperature_runtime_status": "not_extracted_in_source_manifest",
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
        "source.case_data_pair_count",
        len(manifest["case_data_pairs"]) >= config["validation"]["min_case_data_pairs"],
        str(len(manifest["case_data_pairs"])),
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
        "scope": "Fluent C07 heat-transfer case/data source manifest; no Fluent thermal solve or energy-balance extraction",
        "checks": checks,
        "details": {
            "case_data_pairs": manifest["case_data_pairs"],
            "no_claims": config["validation"]["no_claims"],
        },
    }
