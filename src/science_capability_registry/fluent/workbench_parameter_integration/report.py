"""Report writer for Fluent C08 Workbench parameter integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C08 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- outer archive status: {metrics['outer_archive_status']}",
        f"- nested WBPZ status: {metrics['nested_archive_status']}",
        f"- nested entries: {metrics['nested_entry_count']}",
        f"- Workbench version: {metrics['workbench_project_version']}",
        f"- Workbench build: {metrics['workbench_build_version']}",
        f"- current parameter count: {metrics['current_parameter_count']}",
        f"- historical design-point rows: {metrics['historical_design_point_row_count']}",
        f"- Workbench journals: {metrics['workbench_journal_count']}",
        f"- RunWB2 env configured: {metrics['runwb2_env_configured']}",
        f"- Workbench runtime status: {metrics['workbench_runtime_status']}",
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
            "No Workbench headless execution, project migration, design-point update, or Fluent batch equivalence is claimed by this static preflight.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
