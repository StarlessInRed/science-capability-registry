"""Automatic validation for Cantera C02 outputs."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _in_range(value: float, limits: dict[str, float]) -> bool:
    return float(limits["min"]) <= value <= float(limits["max"])


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    limits = config["validation"]
    modes = metrics.get("modes", {})

    for mode_name in limits["required_modes"]:
        _check(
            checks,
            f"mode.{mode_name}.present",
            mode_name in modes,
            f"Mode `{mode_name}` is present in metrics.",
        )

    for mode_name, mode_metrics in modes.items():
        flame_speed = float(mode_metrics.get("flame_speed_m_s", math.nan))
        peak_temperature = float(mode_metrics.get("peak_temperature_k", math.nan))
        temperature_rise = float(mode_metrics.get("burned_temperature_rise_k", math.nan))
        heat_release = float(mode_metrics.get("max_heat_release_rate_w_m3", math.nan))
        grid_count = int(mode_metrics.get("grid_point_count", 0))

        _check(
            checks,
            f"mode.{mode_name}.flame_speed_finite",
            math.isfinite(flame_speed) and flame_speed > 0.0,
            f"Flame speed is {flame_speed:.6g} m/s.",
        )
        _check(
            checks,
            f"mode.{mode_name}.flame_speed_reference_range",
            _in_range(flame_speed, limits["flame_speed_m_s"]),
            (
                f"Expected {limits['flame_speed_m_s']['min']} m/s <= speed <= "
                f"{limits['flame_speed_m_s']['max']} m/s; got {flame_speed:.6g} m/s."
            ),
        )
        _check(
            checks,
            f"mode.{mode_name}.peak_temperature_reference_range",
            _in_range(peak_temperature, limits["peak_temperature_k"]),
            (
                f"Expected {limits['peak_temperature_k']['min']} K <= peak <= "
                f"{limits['peak_temperature_k']['max']} K; got {peak_temperature:.6g} K."
            ),
        )
        _check(
            checks,
            f"mode.{mode_name}.temperature_rise",
            temperature_rise >= float(limits["burned_temperature_rise_k"]["min"]),
            f"Burned gas temperature rise is {temperature_rise:.6g} K.",
        )
        _check(
            checks,
            f"mode.{mode_name}.heat_release_positive",
            heat_release >= float(limits["max_heat_release_rate_w_m3"]["min"]),
            f"Maximum heat release rate is {heat_release:.6g} W/m3.",
        )
        _check(
            checks,
            f"mode.{mode_name}.grid_resolution",
            grid_count >= int(limits["min_grid_points"]),
            f"Grid point count is {grid_count}.",
        )

        tolerance = float(limits["species_bounds_tolerance"])
        for species, bounds in mode_metrics.get("species_bounds", {}).items():
            lower = float(bounds.get("min", math.nan))
            upper = float(bounds.get("max", math.nan))
            finite = bool(bounds.get("finite", False))
            _check(
                checks,
                f"mode.{mode_name}.species_bounds.{species}",
                finite and lower >= -tolerance and upper <= 1.0 + tolerance,
                f"{species} mole fraction range is [{lower:.6g}, {upper:.6g}].",
            )

    if output_dir is not None:
        artifacts = metrics.get("artifacts", {})
        for artifact_name, artifact_path in artifacts.items():
            path = Path(artifact_path)
            if not path.is_absolute():
                path = Path(output_dir) / path
            exists = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.{artifact_name}", exists, f"Artifact path: {path}")

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
