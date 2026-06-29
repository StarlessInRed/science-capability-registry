"""Validation report writer for Cantera C04."""

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
    final = metrics.get("extinction", {})
    rates = final.get("strain_rates_1_s", {})

    lines = [
        f"# Cantera C04 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Width: `{config['width_m']}` m",
        "",
        "## Extinction Metrics",
        "",
        f"- Last burning alpha: `{final.get('alpha')}`",
        f"- Peak temperature: `{final.get('peak_temperature_k')}` K",
        f"- Mean strain rate: `{rates.get('mean')}` 1/s",
        f"- Maximum strain rate: `{rates.get('max')}` 1/s",
        f"- Fuel potential-flow strain rate: `{rates.get('potential_flow_fuel')}` 1/s",
        f"- Oxidizer potential-flow strain rate: `{rates.get('potential_flow_oxidizer')}` 1/s",
        f"- Stoichiometric strain rate: `{rates.get('stoichiometric')}` 1/s",
        f"- Iterations: `{metrics.get('iteration_count')}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{validation['passed']}`",
        "",
    ]

    for check in validation["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- `{status}` `{check['name']}`: {check['details']}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

