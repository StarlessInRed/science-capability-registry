"""Validation report writer for Fluent seed-suite static readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Fluent seed suite {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime profile: {config['fluent']['runtime_profile']}",
        f"- seed count: {metrics['seed_count']}",
        f"- benchmark candidates: {metrics['benchmark_candidate_count']}",
        f"- required modes: {metrics['mode_count']}",
        f"- mismatch classes: {metrics['mismatch_class_count']}",
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
            "This static-readiness report validates the Fluent C01-C08 seed-suite contract, source roles, learning-loop modes, asset links, and artifact completeness. It does not launch Fluent, check out a license, replay tutorial zips, or claim numerical benchmark validation.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
