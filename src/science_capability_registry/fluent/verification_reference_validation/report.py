"""Validation report writer for Fluent C02."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent C02 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- manual case: {config['reference_source']['manual_case_id']}",
        f"- reference title: {config['reference_source']['manual_case_title']}",
        f"- runnable payload status: {metrics['runnable_payload_status']}",
        f"- computed formula pressure drop: {metrics['computed_formula_pressure_drop_pa']:.6g} Pa",
        f"- target pressure drop: {metrics['target_pressure_drop_pa']:.6g} Pa",
        f"- manual Fluent pressure drop: {metrics['manual_fluent_pressure_drop_pa']:.6g} Pa",
        f"- manual relative error: {metrics['manual_relative_error']:.6g}",
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
            "This static-readiness report maps a verification-manual reference into a machine-checkable Fluent C02 contract. It does not launch Fluent, does not claim a local runnable VMFL005 payload, and does not promote the case to benchmark validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
