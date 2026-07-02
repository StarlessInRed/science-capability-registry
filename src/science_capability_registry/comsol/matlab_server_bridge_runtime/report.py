"""Report writer for COMSOL C01."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    env_summary = metrics["environment_summary"]
    lines = [
        f"# COMSOL C01 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime status: {metrics['runtime_status']}",
        f"- required env configured: {env_summary['required_configured_count']} / {env_summary['required_count']}",
        f"- required paths existing: {env_summary['required_existing_count']} / {env_summary['required_count']}",
        f"- MATLAB executed: {metrics['matlab_executed']}",
        f"- finite scalar: {metrics['finite_scalar']}",
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
            "This report covers the COMSOL C01 MATLAB-to-COMSOL bridge boundary. A preflight-only run proves only that the configured environment boundary is complete enough to attempt a future MATLAB LiveLink smoke. It does not claim COMSOL solver execution, physics validation, official model replay, or benchmark validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
