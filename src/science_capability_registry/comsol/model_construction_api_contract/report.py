"""Report writer for COMSOL C02."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    env_summary = metrics["environment_summary"]
    lines = [
        f"# COMSOL C02 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime status: {metrics['runtime_status']}",
        f"- required env configured: {env_summary['required_configured_count']} / {env_summary['required_count']}",
        f"- required paths existing: {env_summary['required_existing_count']} / {env_summary['required_count']}",
        f"- MATLAB executed: {metrics['matlab_executed']}",
        f"- required tag missing count: {metrics['required_tag_missing_count']}",
        f"- duplicate tag count: {metrics['duplicate_tag_count']}",
        f"- finite parameters: {metrics['finite_parameter_count']} / {metrics['parameter_count']}",
        f"- solver executed: {metrics['solver_executed']}",
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
            "This report covers the COMSOL C02 MATLAB-driven model construction contract. A passing smoke means MATLAB/LiveLink constructed an auditable model tree with explicit tags and finite parameters. It does not claim physics assignment completeness, mesh quality, study solve, field extraction, official model replay, or benchmark validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
