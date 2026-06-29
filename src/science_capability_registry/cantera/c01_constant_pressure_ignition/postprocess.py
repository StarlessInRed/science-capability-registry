"""Profile extraction and artifact writers for Cantera C01."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def _max_derivative(time_s: list[float], values: list[float]) -> tuple[float, float, int]:
    best_value = -math.inf
    best_time = math.nan
    best_index = -1
    for index in range(1, len(time_s)):
        dt = time_s[index] - time_s[index - 1]
        if dt <= 0.0:
            continue
        derivative = (values[index] - values[index - 1]) / dt
        if derivative > best_value:
            best_value = derivative
            best_time = time_s[index]
            best_index = index
    return best_time, best_value, best_index


def _peak_time(time_s: list[float], values: list[float]) -> tuple[float, float, int]:
    peak_index = max(range(len(values)), key=values.__getitem__)
    return time_s[peak_index], values[peak_index], peak_index


def _max_abs_step(values: list[float]) -> float:
    if len(values) < 2:
        return math.nan
    return max(abs(values[index] - values[index - 1]) for index in range(1, len(values)))


def write_profile_csv(path: str | Path, profile: dict[str, list[float]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(profile.keys())
    row_count = len(next(iter(profile.values()))) if profile else 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row_index in range(row_count):
            writer.writerow({name: profile[name][row_index] for name in fieldnames})


def summarize_profile(
    profile: dict[str, list[float]],
    tracked_species: list[str],
    ignition_delay_method: str,
) -> dict[str, Any]:
    time_s = profile["time_s"]
    temperature = profile["temperature_k"]
    pressure = profile["pressure_pa"]
    dtdt_time, max_dtdt, dtdt_index = _max_derivative(time_s, temperature)
    oh_time, oh_peak, oh_index = (
        _peak_time(time_s, profile["X_OH"]) if "X_OH" in profile else (math.nan, math.nan, -1)
    )

    if ignition_delay_method == "oh_peak":
        ignition_delay_s = oh_time
    else:
        ignition_delay_s = dtdt_time

    species_bounds: dict[str, dict[str, float | bool]] = {}
    for species in tracked_species:
        column = profile[f"X_{species}"]
        species_bounds[species] = {
            "min": min(column),
            "max": max(column),
            "finite": all(math.isfinite(value) for value in column),
        }

    initial_pressure = pressure[0]
    max_pressure_relative_error = max(
        abs(value - initial_pressure) / initial_pressure for value in pressure
    )

    return {
        "time_point_count": len(time_s),
        "end_time_s": float(time_s[-1]),
        "initial_temperature_k": float(temperature[0]),
        "final_temperature_k": float(temperature[-1]),
        "temperature_rise_k": float(temperature[-1] - temperature[0]),
        "ignition_delay_s": float(ignition_delay_s),
        "ignition_delay_method": ignition_delay_method,
        "max_temperature_derivative_k_s": float(max_dtdt),
        "max_temperature_derivative_time_s": float(dtdt_time),
        "max_temperature_derivative_index": int(dtdt_index),
        "max_temperature_step_k": float(_max_abs_step(temperature)),
        "oh_peak_time_s": float(oh_time),
        "oh_peak_mole_fraction": float(oh_peak),
        "oh_peak_index": int(oh_index),
        "initial_pressure_pa": float(initial_pressure),
        "final_pressure_pa": float(pressure[-1]),
        "max_pressure_relative_error": float(max_pressure_relative_error),
        "species_bounds": species_bounds,
    }
