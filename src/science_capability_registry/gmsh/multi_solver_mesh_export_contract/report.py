"""Validation report writer for Gmsh C06."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# Gmsh C06 {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- source mesh: {config['source_mesh']['source_capability_id']} / {config['source_mesh']['source_case_id']}",
        f"- boundary contract: {config['source_mesh']['boundary_contract_id']}",
        f"- quality contract: {config['source_mesh']['quality_contract_id']}",
        f"- target count: {metrics['target_count']}",
        f"- solver family count: {metrics['solver_family_count']}",
        f"- exported format count: {metrics['exported_format_count']}",
        f"- boundary name mismatches: {metrics['boundary_name_mismatch_count']}",
        f"- successful import count: {metrics['successful_import_count']}",
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
            "This static-readiness report validates the export/import contract only: target solver families, export formats, boundary-name expectations, unit scale, orientation policy, and artifact completeness. It does not claim that any downstream solver import command has been executed.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
