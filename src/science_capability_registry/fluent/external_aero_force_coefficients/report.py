"""Report writer for Fluent C04 reference CSV parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C04 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- archive status: {metrics['archive_status']}",
        f"- archive entries: {metrics['archive_entry_count']}",
        f"- case entries: {metrics['case_entry_count']}",
        f"- mesh entries: {metrics['mesh_entry_count']}",
        f"- reference CSV entries: {metrics['reference_csv_count']}",
        f"- design/table CSV entries: {metrics['design_csv_count']}",
        f"- lift curve monotonic non-decreasing: {metrics['cl_curve_monotonic_non_decreasing']}",
        f"- Cp section count: {metrics['cp_section_count']}",
        f"- force runtime status: {metrics['force_runtime_status']}",
        "",
        "## Reference Rows",
        "",
    ]
    for reference_id, row_count in metrics["reference_row_counts"].items():
        lines.append(f"- {reference_id}: {row_count}")
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
            "No force-coefficient or mesh-independent aero benchmark validation is claimed by this parser-only evidence.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
