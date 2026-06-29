"""Validation report writer for Cantera C03."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_validation_report(
    path: str | Path,
    config: dict[str, Any],
    metrics: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    """Write a compact Markdown validation report."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Cantera C03 Validation Report: {config['case_id']}",
        "",
        "## Case",
        "",
        f"- Capability: `{config['capability_id']}`",
        f"- Mechanism: `{config['mechanism']}`",
        f"- Pressure: `{config['pressure_pa']}` Pa",
        f"- Width: `{config['width_m']}` m",
        "",
        "## Metrics",
        "",
    ]

    for mode_name, mode_metrics in metrics.get("modes", {}).items():
        lines.extend(
            [
                f"### {mode_name}",
                "",
                f"- Converged: `{mode_metrics.get('converged')}`",
                f"- Peak temperature: `{mode_metrics.get('peak_temperature_k')}` K",
                f"- Flame position: `{mode_metrics.get('flame_position_m')}` m",
                f"- Grid points: `{mode_metrics.get('grid_point_count')}`",
                "",
            ]
        )

    comparisons = metrics.get("comparisons", {})
    if comparisons:
        lines.extend(["## Comparisons", ""])
        for name, value in comparisons.items():
            lines.append(f"- `{name}`: `{value}`")
        lines.append("")

    lines.extend(["## Validation", "", f"- Passed: `{validation['passed']}`", ""])
    for check in validation["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- `{status}` `{check['name']}`: {check['details']}")

    if config.get("trend_expectations"):
        lines.extend(["", "## Trend Expectations", ""])
        for item in config["trend_expectations"]:
            lines.append(f"- `{item['parameter']}`: {item['expected_trend']}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

