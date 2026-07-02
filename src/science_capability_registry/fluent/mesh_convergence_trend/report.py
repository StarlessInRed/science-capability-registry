"""Validation report writer for Fluent C03."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C03 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- mesh level count: {metrics['mesh_level_count']}",
        f"- monitored quantity count: {metrics['monitored_quantity_count']}",
        f"- cell counts: {metrics['cell_counts']}",
        f"- runtime status: {metrics['runtime_status']}",
        f"- pressure drops Pa: {metrics.get('pressure_drops_pa', 'not executed')}",
        f"- adjacent pressure-drop changes: {metrics.get('adjacent_pressure_drop_relative_changes', 'not executed')}",
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
            validation["scope"],
            "",
            "No analytical mesh-convergence benchmark validation is claimed until inlet-profile homology and reference parity are closed.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
