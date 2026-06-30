"""Validation report writer for Gmsh C01."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], summary: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    downstream = summary.get("downstream_import", {})
    lines = [
        f"# Gmsh C01 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- node count: {summary.get('node_count')}",
        f"- element count: {summary.get('element_count')}",
        f"- physical groups: {', '.join(sorted(summary.get('physical_groups', {})))}",
        f"- downstream import: {downstream.get('status', 'not_configured')}",
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
            "This report validates deterministic generation of a small parameterized Gmsh geometry and mesh. When configured, it also validates an OpenFOAM gmshToFoam import smoke.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
