"""Validation report writer for Cantera C05."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(
    path: str | Path,
    config: dict[str, Any],
    metrics: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    state = metrics.get("reactor_state", {})
    summary = metrics.get("path_summary", {})

    lines = [
        f"# Cantera C05 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Reactor model: `{config['reactor_model']}`",
        f"- Initial temperature: `{config['initial_temperature_k']}` K",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Composition: `{config['composition']}`",
        f"- Target temperature: `{config['target_temperature_k']}` K",
        f"- Element: `{config['element']}`",
        f"- Label threshold: `{config['diagram']['label_threshold']}`",
        "",
        "## Reactor State",
        "",
        f"- Final temperature: `{state.get('final_temperature_k')}` K",
        f"- Final pressure: `{state.get('final_pressure_pa')}` Pa",
        f"- Final time: `{state.get('final_time_s')}` s",
        f"- Step count: `{state.get('step_count')}`",
        "",
        "## Reaction Path Metrics",
        "",
        f"- Node count: `{summary.get('node_count')}`",
        f"- Nonzero edge count: `{summary.get('edge_count')}`",
        f"- Significant edge count: `{summary.get('significant_edge_count')}`",
        f"- Maximum absolute net flux: `{summary.get('max_abs_net_flux')}`",
        "",
        "## Top Edges",
        "",
    ]

    for edge in summary.get("top_edges", [])[:10]:
        lines.append(
            "- `{}` -> `{}`: abs net flux `{}`".format(
                edge["source"], edge["target"], edge["abs_net_flux"]
            )
        )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Passed: `{validation['passed']}`",
            "",
        ]
    )

    for check in validation["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- `{status}` `{check['name']}`: {check['details']}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
