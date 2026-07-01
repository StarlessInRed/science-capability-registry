"""Shared OpenFOAM evidence envelope helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.config_contract import (
    REPO_ROOT,
    load_json_schema,
    validate_mapping,
)

MANIFEST_SCHEMA_PATH = REPO_ROOT / "schemas" / "openfoam_runtime_evidence_manifest.schema.json"
STANDARD_RESULT_FILES = (
    "manifest.json",
    "metrics.json",
    "validation.json",
    "validation_report.md",
)


def load_evidence_manifest_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(schema_path) if schema_path is not None else MANIFEST_SCHEMA_PATH
    return load_json_schema(path)


def validate_evidence_manifest(
    manifest: dict[str, Any],
    schema_path: str | Path | None = None,
) -> dict[str, Any]:
    schema = load_evidence_manifest_schema(schema_path)
    return validate_mapping(manifest, schema, "OpenFOAM runtime evidence manifest")


def build_runtime_artifacts(
    output_dir: str | Path,
    logs: dict[str, str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result_dir = Path(output_dir)
    artifacts: dict[str, Any] = {
        "result_dir": str(result_dir),
        "required_files": [str(result_dir / file_name) for file_name in STANDARD_RESULT_FILES],
        "logs": logs,
    }
    if extra:
        artifacts.update(extra)
    return artifacts


def write_validation_report(
    path: str | Path,
    title: str,
    validation: dict[str, Any],
    summary_lines: list[str],
    scope: str,
) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status = "passed" if validation.get("passed") else "failed"
    gate = validation.get("gate", "unknown")
    checks = validation.get("checks", [])
    lines = [
        f"# {title}",
        "",
        f"- gate: {gate}",
        f"- status: {status}",
        f"- scope: {scope}",
        "",
        "## Summary",
    ]
    lines.extend(f"- {line}" for line in summary_lines)
    lines.extend(["", "## Checks"])
    if checks:
        for check in checks:
            name = check.get("name", "unnamed_check") if isinstance(check, dict) else str(check)
            passed = check.get("passed", False) if isinstance(check, dict) else False
            check_status = "passed" if passed else "failed"
            lines.append(f"- {name}: {check_status}")
    else:
        lines.append("- no checks recorded")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
