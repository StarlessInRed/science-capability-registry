"""Validation report writer for Gmsh C05."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Gmsh C05 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- field type: {config['size_field']['field_type']}",
        f"- target groups: {', '.join(config['size_field']['target_groups'])}",
        f"- near-wall element count: {metrics['near_wall_element_count']}",
        f"- min near-wall spacing m: {metrics['min_near_wall_spacing_m']}",
        f"- max growth ratio observed: {metrics['max_growth_ratio_observed']}",
        f"- min quality proxy: {metrics['min_quality_proxy']}",
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
            "This static-readiness report validates boundary-layer and size-field configuration semantics only. It reports near-wall mesh metrics separately from global mesh quality and does not claim CFD y+ or downstream solver wall-function validity.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
