"""Validation report writer for Fluent official replay manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent official replay manifest {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- package count: {metrics['package_count']}",
        f"- readable package count: {metrics['readable_package_count']}",
        f"- source entry count: {metrics['source_entry_count']}",
        f"- binding count: {metrics['binding_count']}",
        f"- missing expected entry classes: {metrics['missing_expected_entry_class_count']}",
        "",
        "## Entrypoint Classes",
        "",
    ]
    for name, count in sorted(metrics["entrypoint_class_totals"].items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Checks", ""])
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This manifest reads zip central directories, legacy source directories, and reference files. It does not extract archives, launch Fluent, launch Workbench, or promote tutorial replay to benchmark validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
