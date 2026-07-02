"""Report writer for Fluent C06 sliding/rotating mesh setup."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C06 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- source packages: {metrics['source_package_count']}",
        f"- readable packages: {metrics['readable_package_count']}",
        f"- mesh entries: {metrics['mesh_entry_count']}",
        f"- mesh format counts: {metrics['mesh_format_counts']}",
        f"- total mesh bytes: {metrics['total_mesh_bytes']}",
        f"- solver replay status: {metrics['solver_replay_status']}",
    ]
    if "fluent_return_code" in metrics:
        lines.extend(
            [
                f"- Fluent return code: {metrics['fluent_return_code']}",
                f"- mesh cell count: {metrics['mesh_cell_count']}",
                f"- mesh check completed: {metrics['mesh_check_completed']}",
                f"- Fluent warnings: {metrics['fluent_warning_count']}",
                f"- Fluent errors: {metrics['fluent_error_count']}",
            ]
        )
    lines.extend(["", "## Checks", ""])
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
            "No moving-zone settings, sliding interface setup, transient history, or rotating-machinery validation is claimed by this mesh/setup manifest.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
