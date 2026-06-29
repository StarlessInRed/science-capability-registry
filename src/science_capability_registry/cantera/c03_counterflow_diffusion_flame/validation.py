"""Automatic validation for Cantera C03 outputs."""

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
    """Validate solver metrics, physical bounds, and artifact completeness."""
    checks: list[dict[str, Any]] = []
    modes = metrics.get("modes", {})
    required_modes = [mode["mode"] for mode in config["radiation_modes"]]

    for mode_name in required_modes:
        mode_metrics = modes.get(mode_name)
        _check(checks, f"{mode_name}.exists", mode_metrics is not None, "Mode metrics exist.")
        if not mode_metrics:
            continue
        _check(
            checks,
            f"{mode_name}.converged",
            mode_metrics.get("converged") is True,
            "Solver reported convergence for this mode.",
        )
        peak_temperature = float(mode_metrics.get("peak_temperature_k", math.nan))
        flame_position = float(mode_metrics.get("flame_position_m", math.nan))
        _check(
            checks,
            f"{mode_name}.peak_temperature_finite",
            math.isfinite(peak_temperature),
            f"Peak temperature is {peak_temperature:.6g} K.",
        )
        _check(
            checks,
            f"{mode_name}.flame_position_inside_domain",
            math.isfinite(flame_position) and 0.0 <= flame_position <= float(config["width_m"]),
            f"Flame position is {flame_position:.6g} m.",
        )
        tolerance = float(config["validation"]["species_mole_fraction_tolerance"])
        for species, bounds in mode_metrics.get("species_bounds", {}).items():
            lower = float(bounds["min"])
            upper = float(bounds["max"])
            finite = bool(bounds.get("finite", True))
            bounded = finite and lower >= -tolerance and upper <= 1.0 + tolerance
            _check(
                checks,
                f"{mode_name}.{species}.mole_fraction_bounds",
                bounded,
                f"{species} mole fraction range is [{lower:.6g}, {upper:.6g}].",
            )

    no_rad = modes.get("no_radiation")
    radiation = modes.get("radiation")
    if no_rad:
        limits = config["validation"]["no_radiation_peak_temperature_k"]
        peak_temperature = float(no_rad.get("peak_temperature_k", math.nan))
        _check(
            checks,
            "no_radiation.peak_temperature_reference_range",
            _in_range(peak_temperature, limits),
            f"Expected {limits['min']} K <= peak <= {limits['max']} K; got {peak_temperature:.6g} K.",
        )
        position_limits = config["validation"]["flame_position_m"]
        flame_position = float(no_rad.get("flame_position_m", math.nan))
        _check(
            checks,
            "no_radiation.flame_position_reference_range",
            _in_range(flame_position, position_limits),
            (
                f"Expected {position_limits['min']} m <= position <= "
                f"{position_limits['max']} m; got {flame_position:.6g} m."
            ),
        )

    if no_rad and radiation:
        no_rad_peak = float(no_rad.get("peak_temperature_k", math.nan))
        radiation_peak = float(radiation.get("peak_temperature_k", math.nan))
        _check(
            checks,
            "radiation.peak_temperature_not_higher",
            math.isfinite(no_rad_peak) and math.isfinite(radiation_peak) and radiation_peak <= no_rad_peak,
            f"Radiation peak {radiation_peak:.6g} K; no-radiation peak {no_rad_peak:.6g} K.",
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

