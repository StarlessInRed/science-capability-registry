"""Validation report writer for Gmsh C04."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Gmsh C04 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- CAD source: {config['cad_source']['source_ref']}",
        f"- CAD format: {config['cad_source']['cad_format']}",
        f"- imported entity count: {metrics['imported_entity_count']}",
        f"- healed entity count: {metrics['healed_entity_count']}",
        f"- deleted entity count: {metrics['deleted_entity_count']}",
        f"- duplicate or sliver count: {metrics['duplicate_or_sliver_count']}",
        f"- unassigned entity count: {metrics['unassigned_entity_count']}",
        "",
        "## Checks",
        "",
    ]
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This static-readiness report validates CAD import and healing contract semantics only. It separates imported/modified/deleted/new entity accounting from mesh generation and does not claim that OpenCASCADE import has executed.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
