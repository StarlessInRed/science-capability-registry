"""Report writer for Fluent C01."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    mass_balance = metrics.get("mass_balance", {})
    lines = [
        f"# Fluent C01 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- dimension precision: {config['fluent']['dimension_precision']}",
        f"- iteration rows parsed: {metrics['completed_iteration_count']}",
        f"- max residual: {metrics['max_residual']}",
        f"- mass imbalance fraction: {mass_balance.get('mass_imbalance_fraction')}",
        f"- pressure drop status: {metrics['pressure_drop_status']}",
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
            "This smoke report proves that the configured local Fluent executable can run a legacy standalone elbow case in headless batch mode, read case/data, perform a bounded iteration, emit a mass-flow report, and write case/data artifacts. It does not claim verification-manual benchmark validation or pressure-drop validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
