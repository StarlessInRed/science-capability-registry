"""Validation report writer for Cantera C01."""

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
    summary = metrics.get("summary", {})

    lines = [
        f"# Cantera C01 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Reactor model: `{config['reactor_model']}`",
        f"- Initial temperature: `{config['initial_temperature_k']}` K",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Composition: `{config['composition']}`",
        "",
        "## Ignition Metrics",
        "",
        f"- Ignition delay: `{summary.get('ignition_delay_s')}` s",
        f"- Ignition delay method: `{summary.get('ignition_delay_method')}`",
        f"- Final temperature: `{summary.get('final_temperature_k')}` K",
        f"- Temperature rise: `{summary.get('temperature_rise_k')}` K",
        f"- Maximum dT/dt: `{summary.get('max_temperature_derivative_k_s')}` K/s",
        f"- OH peak mole fraction: `{summary.get('oh_peak_mole_fraction')}`",
        f"- Maximum relative pressure error: `{summary.get('max_pressure_relative_error')}`",
        f"- Time points: `{summary.get('time_point_count')}`",
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
