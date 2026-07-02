"""Report writer for Fluent C05 VOF source setup."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C05 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- archive status: {metrics['archive_status']}",
        f"- archive entries: {metrics['archive_entry_count']}",
        f"- mesh entries: {metrics['mesh_entry_count']}",
        f"- mesh format counts: {metrics['mesh_format_counts']}",
        f"- total mesh bytes: {metrics['total_mesh_bytes']}",
        f"- solver replay status: {metrics['solver_replay_status']}",
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
            "No VOF transient solve, alpha boundedness, interface motion, or conservation validation is claimed by this mesh/setup manifest.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
