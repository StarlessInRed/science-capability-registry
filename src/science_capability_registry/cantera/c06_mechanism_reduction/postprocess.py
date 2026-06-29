"""Post-processing helpers for Cantera C06 mechanism reduction."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def ignition_delay_from_profile(time_ms: list[float], temperature_k: list[float]) -> float:
    if len(time_ms) < 2:
        return math.nan
    best_value = -math.inf
    best_time = math.nan
    for index in range(1, len(time_ms)):
        dt_s = (time_ms[index] - time_ms[index - 1]) * 1.0e-3
        if dt_s <= 0.0:
            continue
        derivative = (temperature_k[index] - temperature_k[index - 1]) / dt_s
        if derivative > best_value:
            best_value = derivative
            best_time = time_ms[index]
    return float(best_time)


def summarize_profile(profile: dict[str, list[float]]) -> dict[str, float | int]:
    time_ms = profile["time_ms"]
    temperature = profile["temperature_k"]
    return {
        "time_point_count": len(time_ms),
        "final_time_ms": float(time_ms[-1]) if time_ms else math.nan,
        "initial_temperature_k": float(temperature[0]) if temperature else math.nan,
        "final_temperature_k": float(temperature[-1]) if temperature else math.nan,
        "max_temperature_k": float(max(temperature)) if temperature else math.nan,
        "temperature_rise_k": float(temperature[-1] - temperature[0]) if temperature else math.nan,
        "ignition_delay_ms": ignition_delay_from_profile(time_ms, temperature),
    }


def compare_summary(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    reference_tau = float(reference["ignition_delay_ms"])
    candidate_tau = float(candidate["ignition_delay_ms"])
    reference_final_temperature = float(reference["final_temperature_k"])
    candidate_final_temperature = float(candidate["final_temperature_k"])
    if math.isfinite(reference_tau) and reference_tau > 0.0 and math.isfinite(candidate_tau):
        tau_error = abs(candidate_tau - reference_tau) / reference_tau
    else:
        tau_error = math.inf
    return {
        "ignition_delay_relative_error": float(tau_error),
        "final_temperature_error_k": float(
            abs(candidate_final_temperature - reference_final_temperature)
        ),
    }


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


def write_ranking_csv(path: str | Path, ranking: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["rank", "score", "equation"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in ranking:
            writer.writerow({name: row[name] for name in fieldnames})


def write_reduction_summary_csv(path: str | Path, reductions: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "requested_reaction_count",
        "species_count",
        "reaction_count",
        "time_point_count",
        "ignition_delay_ms",
        "ignition_delay_relative_error",
        "final_temperature_k",
        "final_temperature_error_k",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in reductions:
            writer.writerow({name: row.get(name) for name in fieldnames})


def plot_temperature_profiles(
    plt: Any,
    baseline: dict[str, Any],
    reductions: list[dict[str, Any]],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    baseline_profile = baseline["profile"]
    ax.plot(
        baseline_profile["time_ms"],
        baseline_profile["temperature_k"],
        color="black",
        linewidth=2.5,
        label=f"K={baseline['species_count']}, R={baseline['reaction_count']}",
    )
    for result in reductions:
        profile = result["profile"]
        ax.plot(
            profile["time_ms"],
            profile["temperature_k"],
            linewidth=1.5,
            label=f"K={result['species_count']}, R={result['reaction_count']}",
        )
    ax.set_xlabel("time [ms]")
    ax.set_ylabel("temperature [K]")
    ax.set_title("Reduced mechanism ignition temperature profiles")
    ax.set_xlim(0, max(baseline_profile["time_ms"]))
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
