"""Automatic validation for Cantera C01 outputs."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _in_range(value: float, limits: dict[str, float]) -> bool:
    return float(limits["min"]) <= value <= float(limits["max"])


def _finite_sequence(values: list[Any]) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except (TypeError, ValueError):
        return False


def _expected_artifacts(config: dict[str, Any]) -> list[str]:
    outputs = config["outputs"]
    expected: list[str] = []
    if outputs["save_csv"]:
        expected.append("ignition_profile.csv")
    if outputs["save_plots"]:
        expected.append("ignition_temperature_species.png")
    if outputs["save_log"]:
        expected.append("ignition_run.log")
    if outputs["save_metrics"]:
        expected.append("metrics.json")
    if outputs["save_validation_report"]:
        expected.append("validation_report.md")
    return expected


def _profile_lengths(profile: dict[str, Any]) -> dict[str, int]:
    lengths: dict[str, int] = {}
    for key, values in profile.items():
        lengths[key] = len(values) if isinstance(values, list) else -1
    return lengths


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    limits = config["validation"]
    summary = metrics.get("summary", {})
    profile = metrics.get("profile", {})

    final_temperature = float(summary.get("final_temperature_k", math.nan))
    temperature_rise = float(summary.get("temperature_rise_k", math.nan))
    ignition_delay = float(summary.get("ignition_delay_s", math.nan))
    time_points = int(summary.get("time_point_count", 0))
    pressure_error = float(summary.get("max_pressure_relative_error", math.nan))
    max_dtdt = float(summary.get("max_temperature_derivative_k_s", math.nan))
    end_time = float(summary.get("end_time_s", math.nan))
    initial_temperature = float(summary.get("initial_temperature_k", math.nan))
    max_temperature_step = float(summary.get("max_temperature_step_k", math.nan))

    profile_present = isinstance(profile, dict) and bool(profile)
    _check(checks, "profile.present", profile_present, "Metrics include raw time-series profile.")

    if profile_present:
        lengths = _profile_lengths(profile)
        row_count = lengths.get("time_s", -1)
        equal_lengths = row_count > 0 and all(length == row_count for length in lengths.values())
        _check(
            checks,
            "profile.equal_lengths",
            equal_lengths,
            f"Profile column lengths: {lengths}.",
        )
        required_columns = [
            "time_s",
            "time_ms",
            "temperature_k",
            "pressure_pa",
            "internal_energy_j_kg",
            "enthalpy_j_kg",
        ]
        required_columns.extend(f"X_{species}" for species in config["outputs"]["tracked_species"])
        for column in required_columns:
            values = profile.get(column)
            _check(
                checks,
                f"profile.column.{column}",
                isinstance(values, list) and len(values) == row_count and _finite_sequence(values),
                f"Column {column} length is {len(values) if isinstance(values, list) else 'missing'}.",
            )

        time_s = profile.get("time_s", [])
        if isinstance(time_s, list) and row_count > 1:
            monotonic = all(
                float(time_s[index]) > float(time_s[index - 1]) for index in range(1, row_count)
            )
            max_time_step = max(
                float(time_s[index]) - float(time_s[index - 1]) for index in range(1, row_count)
            )
        else:
            monotonic = False
            max_time_step = math.nan
        _check(checks, "profile.time_monotonic", monotonic, "time_s is strictly increasing.")
        _check(
            checks,
            "integration.max_time_step",
            math.isfinite(max_time_step) and max_time_step <= float(limits["max_time_step_s"]),
            f"Maximum saved time step is {max_time_step:.6g} s.",
        )

    _check(
        checks,
        "integration.time_points",
        time_points >= int(limits["min_time_points"]),
        f"Time point count is {time_points}.",
    )
    _check(
        checks,
        "integration.end_time",
        math.isfinite(end_time)
        and end_time >= float(config["advance"]["t_end_s"])
        and end_time <= float(config["advance"]["t_end_s"]) + float(limits["end_time_tolerance_s"]),
        f"End time is {end_time:.6g} s for requested {config['advance']['t_end_s']:.6g} s.",
    )
    _check(
        checks,
        "temperature.initial_matches_config",
        math.isfinite(initial_temperature)
        and abs(initial_temperature - float(config["initial_temperature_k"]))
        <= float(limits["initial_temperature_tolerance_k"]),
        f"Initial profile temperature is {initial_temperature:.6g} K.",
    )
    _check(
        checks,
        "temperature.final_reference_range",
        _in_range(final_temperature, limits["final_temperature_k"]),
        (
            f"Expected {limits['final_temperature_k']['min']} K <= final <= "
            f"{limits['final_temperature_k']['max']} K; got {final_temperature:.6g} K."
        ),
    )
    _check(
        checks,
        "temperature.rise",
        temperature_rise >= float(limits["temperature_rise_k"]["min"]),
        f"Temperature rise is {temperature_rise:.6g} K.",
    )
    _check(
        checks,
        "ignition_delay.finite_positive",
        math.isfinite(ignition_delay) and ignition_delay > 0.0,
        f"Ignition delay is {ignition_delay:.6g} s.",
    )
    _check(
        checks,
        "ignition_delay.reference_range",
        _in_range(ignition_delay, limits["ignition_delay_s"]),
        (
            f"Expected {limits['ignition_delay_s']['min']} s <= tau <= "
            f"{limits['ignition_delay_s']['max']} s; got {ignition_delay:.6g} s."
        ),
    )
    _check(
        checks,
        "temperature.max_derivative_positive",
        math.isfinite(max_dtdt) and max_dtdt > 0.0,
        f"Maximum dT/dt is {max_dtdt:.6g} K/s.",
    )
    _check(
        checks,
        "temperature.advance_limit",
        math.isfinite(max_temperature_step)
        and max_temperature_step <= float(limits["max_temperature_step_k"]),
        f"Maximum saved temperature step is {max_temperature_step:.6g} K.",
    )
    _check(
        checks,
        "pressure.constant",
        pressure_error <= float(limits["max_pressure_relative_error"]),
        f"Maximum relative pressure error is {pressure_error:.6g}.",
    )
    _check(
        checks,
        "ignition_delay.method",
        summary.get("ignition_delay_method") == config["ignition_delay_method"],
        f"Summary method is {summary.get('ignition_delay_method')}.",
    )
    if config["ignition_delay_method"] == "oh_peak":
        _check(
            checks,
            "ignition_delay.oh_species_tracked",
            "OH" in config["outputs"]["tracked_species"],
            "OH must be tracked for oh_peak ignition delay.",
        )
        ignition_index = int(summary.get("oh_peak_index", -1))
    else:
        ignition_index = int(summary.get("max_temperature_derivative_index", -1))
    boundary_margin = int(limits["ignition_delay_boundary_margin_points"])
    _check(
        checks,
        "ignition_delay.not_boundary",
        ignition_index >= boundary_margin and ignition_index <= time_points - 1 - boundary_margin,
        f"Ignition index is {ignition_index} in {time_points} saved points.",
    )

    tolerance = float(limits["species_bounds_tolerance"])
    species_bounds = summary.get("species_bounds", {})
    for species in config["outputs"]["tracked_species"]:
        bounds = species_bounds.get(species, {})
        lower = float(bounds.get("min", math.nan))
        upper = float(bounds.get("max", math.nan))
        finite = bool(bounds.get("finite", False))
        _check(
            checks,
            f"species_bounds.{species}",
            finite and lower >= -tolerance and upper <= 1.0 + tolerance,
            f"{species} mole fraction range is [{lower:.6g}, {upper:.6g}].",
        )

    if output_dir is not None:
        artifacts = metrics.get("artifacts", {})
        for artifact_name in _expected_artifacts(config):
            artifact_path = artifacts.get(artifact_name)
            path = Path(artifact_path) if artifact_path else Path(output_dir) / artifact_name
            if not path.is_absolute():
                path = Path(output_dir) / path
            exists = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.{artifact_name}", exists, f"Artifact path: {path}")

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
