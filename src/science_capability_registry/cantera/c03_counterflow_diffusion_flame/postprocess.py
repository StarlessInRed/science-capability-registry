"""Profile extraction and artifact writers for Cantera C03."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def _sequence_to_float_list(values: Any) -> list[float]:
    return [float(value) for value in values]


def extract_profile(flame: Any, gas: Any, species_names: list[str]) -> dict[str, list[float]]:
    """Extract grid, flow fields, temperature, and selected mole fractions."""
    grid = _sequence_to_float_list(flame.grid)
    temperature = _sequence_to_float_list(flame.T)
    velocity = _sequence_to_float_list(flame.velocity)
    spread_rate_raw = getattr(flame, "spread_rate", [math.nan] * len(grid))
    spread_rate = _sequence_to_float_list(spread_rate_raw)

    profile: dict[str, list[float]] = {
        "grid_m": grid,
        "velocity_m_s": velocity,
        "spread_rate_1_s": spread_rate,
        "temperature_k": temperature,
    }

    mole_fractions = flame.X
    for species in species_names:
        index = gas.species_index(species)
        profile[f"X_{species}"] = _sequence_to_float_list(mole_fractions[index])

    return profile


def write_profile_csv(path: str | Path, profile: dict[str, list[float]]) -> None:
    """Write an extracted profile to CSV."""
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
    """Calculate machine-readable scalar metrics from a profile."""
    temperatures = profile["temperature_k"]
    grid = profile["grid_m"]
    peak_index = max(range(len(temperatures)), key=temperatures.__getitem__)
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
        "peak_temperature_k": float(temperatures[peak_index]),
        "flame_position_m": float(grid[peak_index]),
        "grid_point_count": len(grid),
        "species_bounds": species_bounds,
    }

