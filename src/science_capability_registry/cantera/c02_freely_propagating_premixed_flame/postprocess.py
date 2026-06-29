"""Profile extraction and artifact writers for Cantera C02."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def _sequence_to_float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def extract_profile(flame: Any, gas: Any, species_names: list[str]) -> dict[str, list[float]]:
    """Extract grid, flow fields, temperature, heat release, and selected mole fractions."""
    grid = _sequence_to_float_list(flame.grid)
    profile: dict[str, list[float]] = {
        "grid_m": grid,
        "velocity_m_s": _sequence_to_float_list(flame.velocity),
        "temperature_k": _sequence_to_float_list(flame.T),
        "density_kg_m3": _sequence_to_float_list(getattr(flame, "density", [math.nan] * len(grid))),
        "heat_release_rate_w_m3": _sequence_to_float_list(
            getattr(flame, "heat_release_rate", [math.nan] * len(grid))
        ),
    }

    mole_fractions = flame.X
    for species in species_names:
        index = gas.species_index(species)
        profile[f"X_{species}"] = _sequence_to_float_list(mole_fractions[index])

    return profile


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


def summarize_profile(profile: dict[str, list[float]], species_names: list[str]) -> dict[str, Any]:
    temperatures = profile["temperature_k"]
    grid = profile["grid_m"]
    heat_release = profile["heat_release_rate_w_m3"]
    peak_temperature_index = max(range(len(temperatures)), key=temperatures.__getitem__)
    heat_release_index = max(range(len(heat_release)), key=heat_release.__getitem__)
    species_bounds: dict[str, dict[str, float | bool]] = {}

    for species in species_names:
        column = profile[f"X_{species}"]
        finite = all(math.isfinite(value) for value in column)
        species_bounds[species] = {
            "min": min(column),
            "max": max(column),
            "finite": finite,
        }

    return {
        "peak_temperature_k": float(temperatures[peak_temperature_index]),
        "peak_temperature_position_m": float(grid[peak_temperature_index]),
        "burned_temperature_k": float(temperatures[-1]),
        "unburned_temperature_k": float(temperatures[0]),
        "burned_temperature_rise_k": float(temperatures[-1] - temperatures[0]),
        "max_heat_release_rate_w_m3": float(heat_release[heat_release_index]),
        "flame_position_m": float(grid[heat_release_index]),
        "grid_point_count": len(grid),
        "species_bounds": species_bounds,
    }
