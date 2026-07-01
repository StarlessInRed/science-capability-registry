"""Validation report writer for Gmsh C03."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Gmsh C03 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- geometry source: {config['geometry_contract']['source_capability_id']} / {config['geometry_contract']['source_case_id']}",
        f"- boundary contract: {config['geometry_contract']['boundary_contract_id']}",
        f"- level count: {metrics['level_count']}",
        f"- characteristic length monotonic: {metrics['characteristic_length_monotonic']}",
        f"- element count monotonic: {metrics['element_count_monotonic']}",
        f"- min quality proxy: {metrics['min_quality_proxy']}",
        f"- max aspect ratio proxy: {metrics['max_aspect_ratio_proxy']}",
        f"- quality drop fraction: {metrics['quality_drop_fraction']:.3f}",
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
            "This static-readiness report validates refinement and quality trend semantics only. It does not claim that Gmsh has generated meshes for these levels, and it keeps solver accuracy or solver import validation outside C03.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
