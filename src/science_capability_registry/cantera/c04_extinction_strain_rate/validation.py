"""Automatic validation for Cantera C04 outputs."""

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
    history = metrics.get("history", {})
    final = metrics.get("extinction", {})

    alpha = history.get("alpha", [])
    temperatures = history.get("peak_temperature_k", [])
    strain_rates = history.get("max_strain_rate_1_s", [])
    statuses = history.get("status", [])

    _check(
        checks,
        "history.lengths_match",
        len(alpha) == len(temperatures) == len(strain_rates) == len(statuses) and len(alpha) > 0,
        f"History lengths: alpha={len(alpha)}, T={len(temperatures)}, a_max={len(strain_rates)}, status={len(statuses)}.",
    )
    _check(
        checks,
        "history.has_burning_solution",
        statuses.count("burning") >= int(limits["min_burning_solution_count"]),
        f"Burning solution count is {statuses.count('burning')}.",
    )
    _check(
        checks,
        "history.has_extinguished_solution",
        "extinguished" in statuses,
        "At least one extinguished solution was detected.",
    )

    peak_temperature = float(final.get("peak_temperature_k", math.nan))
    max_strain_rate = float(final.get("strain_rates_1_s", {}).get("max", math.nan))
    temperature_limits = limits["extinction_peak_temperature_k"]
    strain_limits = limits["max_strain_rate_1_s"]

    _check(
        checks,
        "extinction.peak_temperature_finite",
        math.isfinite(peak_temperature),
        f"Peak temperature is {peak_temperature:.6g} K.",
    )
    _check(
        checks,
        "extinction.peak_temperature_reference_range",
        _in_range(peak_temperature, temperature_limits),
        (
            f"Expected {temperature_limits['min']} K <= peak <= "
            f"{temperature_limits['max']} K; got {peak_temperature:.6g} K."
        ),
    )
    _check(
        checks,
        "extinction.max_strain_rate_reference_range",
        _in_range(max_strain_rate, strain_limits),
        (
            f"Expected {strain_limits['min']} 1/s <= a_max <= "
            f"{strain_limits['max']} 1/s; got {max_strain_rate:.6g} 1/s."
        ),
    )

    for rate_name in [
        "mean",
        "max",
        "potential_flow_fuel",
        "potential_flow_oxidizer",
        "stoichiometric",
    ]:
        value = float(final.get("strain_rates_1_s", {}).get(rate_name, math.nan))
        _check(
            checks,
            f"extinction.strain_rate.{rate_name}",
            math.isfinite(value) and value > 0.0,
            f"{rate_name} strain rate is {value:.6g} 1/s.",
        )

    if temperatures:
        temperature_limit = max(
            float(config["fuel_inlet"]["temperature_k"]),
            float(config["oxidizer_inlet"]["temperature_k"]),
        )
        _check(
            checks,
            "history.extinction_temperature_drop",
            min(temperatures) <= temperature_limit + 1.0,
            f"Minimum recorded peak temperature is {min(temperatures):.6g} K.",
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

