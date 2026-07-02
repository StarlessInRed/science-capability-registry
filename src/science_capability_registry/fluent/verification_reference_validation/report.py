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
    ]
    if "fluent_return_code" in metrics:
        lines.extend(
            [
                f"- Fluent return code: {metrics['fluent_return_code']}",
                f"- mesh cell count: {metrics['mesh_cell_count']} / expected {metrics['expected_mesh_cell_count']}",
                f"- mesh check completed: {metrics['mesh_check_completed']}",
                f"- Fluent warnings: {metrics['fluent_warning_count']}",
                f"- Fluent errors: {metrics['fluent_error_count']}",
                f"- pressure-drop runtime status: {metrics['pressure_drop_runtime_status']}",
            ]
        )
    if "solution_converged" in metrics:
        final_residuals = metrics.get("final_residuals", {})
        lines.extend(
            [
                f"- solution converged: {metrics['solution_converged']}",
                f"- iteration count: {metrics['iteration_count']}",
                f"- final continuity residual: {final_residuals.get('continuity')}",
                f"- final x-velocity residual: {final_residuals.get('x_velocity')}",
                f"- final y-velocity residual: {final_residuals.get('y_velocity')}",
            ]
        )
    lines.extend(["", "## Checks", ""])
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            validation["scope"],
            "",
            "No pressure-drop benchmark validation is claimed unless this report explicitly includes a Fluent pressure-drop solve and mesh-trend closure.",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
