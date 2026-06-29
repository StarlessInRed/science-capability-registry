"""Validation report writer for Cantera C06."""

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
    baseline = metrics.get("baseline", {})
    baseline_summary = baseline.get("summary", {})

    lines = [
        f"# Cantera C06 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Reactor model: `{config['reactor_model']}`",
        f"- Initial temperature: `{config['initial_temperature_k']}` K",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Equivalence ratio: `{config['equivalence_ratio']}`",
        f"- Fuel: `{config['fuel']}`",
        f"- Oxidizer: `{config['oxidizer']}`",
        f"- End time: `{config['simulation']['end_time_s']}` s",
        "",
        "## Full Mechanism",
        "",
        f"- Species count: `{baseline.get('species_count')}`",
        f"- Reaction count: `{baseline.get('reaction_count')}`",
        f"- Ignition delay: `{baseline_summary.get('ignition_delay_ms')}` ms",
        f"- Final temperature: `{baseline_summary.get('final_temperature_k')}` K",
        "",
        "## Reduced Mechanisms",
        "",
        "| Requested reactions | Species | Reactions | Ignition delay ms | Tau rel. error | Final T K | Final T error K |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in metrics.get("reductions", []):
        lines.append(
            "| {requested_reaction_count} | {species_count} | {reaction_count} | "
            "{ignition_delay_ms} | {ignition_delay_relative_error} | "
            "{final_temperature_k} | {final_temperature_error_k} |".format(**row)
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
