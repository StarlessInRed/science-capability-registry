"""Report writer for Fluent C07 heat-transfer source readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C07 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- archive status: {metrics['archive_status']}",
        f"- archive entries: {metrics['archive_entry_count']}",
        f"- case entries: {metrics['case_entry_count']}",
        f"- data entries: {metrics['data_entry_count']}",
        f"- case/data pairs: {metrics['case_data_pair_count']}",
        f"- total uncompressed bytes: {metrics['total_uncompressed_bytes']}",
        f"- heat-rate runtime status: {metrics['heat_rate_runtime_status']}",
        f"- temperature runtime status: {metrics['temperature_runtime_status']}",
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
            "No heat-rate balance, temperature extrema, or CHT benchmark validation is claimed by this source-manifest evidence.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
