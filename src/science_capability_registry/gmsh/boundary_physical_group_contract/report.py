"""Validation report writer for Gmsh C02."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    role_coverage = metrics["role_mapping_coverage"]
    lines = [
        f"# Gmsh C02 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- geometry source: {config['geometry']['source_capability_id']} / {config['geometry']['source_case_id']}",
        f"- physical group count: {metrics['physical_group_count']}",
        f"- missing required groups: {metrics['missing_required_group_count']}",
        f"- duplicate names: {metrics['duplicate_name_count']}",
        f"- dimension-role errors: {metrics['dimension_role_error_count']}",
        f"- downstream target: {config['downstream_boundary_map']['target_solver']}",
        f"- downstream role coverage: {role_coverage:.3f}",
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
            "This static-readiness report validates boundary semantics only: group names, dimensions, solver-facing roles, required-group presence, downstream role mapping, and artifact completeness. It does not claim Gmsh mesh generation success, downstream solver import success, or CFD/FEM boundary-condition correctness.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
