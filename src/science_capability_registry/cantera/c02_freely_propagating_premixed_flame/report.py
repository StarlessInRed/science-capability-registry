"""Validation report writer for Cantera C02."""

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

    lines = [
        f"# Cantera C02 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Reactants: `{config['reactants']}`",
        f"- Width: `{config['width_m']}` m",
        "",
        "## Flame Metrics",
        "",
    ]

    for mode_name, mode_metrics in metrics.get("modes", {}).items():
        lines.extend(
            [
                f"### `{mode_name}`",
                "",
                f"- Flame speed: `{mode_metrics.get('flame_speed_m_s')}` m/s",
                f"- Peak temperature: `{mode_metrics.get('peak_temperature_k')}` K",
                f"- Burned temperature: `{mode_metrics.get('burned_temperature_k')}` K",
                f"- Flame position: `{mode_metrics.get('flame_position_m')}` m",
                f"- Maximum heat release rate: `{mode_metrics.get('max_heat_release_rate_w_m3')}` W/m3",
                f"- Grid points: `{mode_metrics.get('grid_point_count')}`",
                "",
            ]
        )

    lines.extend(
        [
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
