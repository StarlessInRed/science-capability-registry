"""Post-processing helpers for C08 shock metrics."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

PROFILE_COLUMNS = ["x_m", "p", "rho", "T", "Ux", "Uy", "Uz"]


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot average an empty value set.")
    return sum(values) / len(values)


def locate_shock_position_from_profile(rows: list[dict[str, float]], quantity: str = "p") -> float:
    ordered = sorted(rows, key=lambda row: float(row["x_m"]))
    if len(ordered) < 2:
        raise ValueError("At least two profile samples are required to locate a shock.")
    gradients: list[tuple[float, float]] = []
    for left, right in zip(ordered, ordered[1:]):
        dx = float(right["x_m"]) - float(left["x_m"])
        if dx <= 0.0:
            continue
        gradient = abs((float(right[quantity]) - float(left[quantity])) / dx)
        gradients.append(((float(left["x_m"]) + float(right["x_m"])) / 2.0, gradient))
    if not gradients:
        raise ValueError("Profile x coordinates must be strictly increasing after sorting.")
    return max(gradients, key=lambda item: item[1])[0]


def average_state_windows(
    rows: list[dict[str, float]],
    upstream_window_m: tuple[float, float] | list[float],
    downstream_window_m: tuple[float, float] | list[float],
) -> dict[str, dict[str, float]]:
    upstream_start, upstream_stop = float(upstream_window_m[0]), float(upstream_window_m[1])
    downstream_start, downstream_stop = float(downstream_window_m[0]), float(downstream_window_m[1])
    if upstream_start >= upstream_stop or downstream_start >= downstream_stop:
        raise ValueError("Averaging windows must have increasing bounds.")
    if upstream_stop >= downstream_start:
        raise ValueError("Upstream and downstream windows must be non-overlapping and ordered left-to-right.")

    upstream = [row for row in rows if upstream_start <= float(row["x_m"]) <= upstream_stop]
    downstream = [row for row in rows if downstream_start <= float(row["x_m"]) <= downstream_stop]
    if not upstream or not downstream:
        raise ValueError("Both upstream and downstream windows must contain samples.")

    def summarize(sample: list[dict[str, float]]) -> dict[str, float]:
        ux_values = [float(row.get("Ux", 0.0)) for row in sample]
        uy_values = [float(row.get("Uy", 0.0)) for row in sample]
        uz_values = [float(row.get("Uz", 0.0)) for row in sample]
        return {
            "p": _mean([float(row["p"]) for row in sample]),
            "rho": _mean([float(row["rho"]) for row in sample]),
            "T": _mean([float(row.get("T", 0.0)) for row in sample]),
            "U_mag": _mean([math.sqrt(ux * ux + uy * uy + uz * uz) for ux, uy, uz in zip(ux_values, uy_values, uz_values)]),
        }

    return {"upstream": summarize(upstream), "downstream": summarize(downstream)}


def compute_jump_ratios(upstream: dict[str, float], downstream: dict[str, float]) -> dict[str, float]:
    if upstream["p"] <= 0.0 or upstream["rho"] <= 0.0:
        raise ValueError("Upstream pressure and density must be positive.")
    return {
        "pressure_jump_ratio": downstream["p"] / upstream["p"],
        "density_jump_ratio": downstream["rho"] / upstream["rho"],
    }


def normal_shock_sanity_ratios(mach: float, gamma: float = 1.4) -> dict[str, float]:
    if mach <= 1.0:
        raise ValueError("Normal-shock sanity ratios require supersonic upstream Mach.")
    if gamma <= 1.0:
        raise ValueError("Specific heat ratio gamma must be greater than one.")
    mach2 = mach * mach
    pressure_ratio = 1.0 + (2.0 * gamma / (gamma + 1.0)) * (mach2 - 1.0)
    density_ratio = ((gamma + 1.0) * mach2) / ((gamma - 1.0) * mach2 + 2.0)
    return {"pressure_jump_ratio": pressure_ratio, "density_jump_ratio": density_ratio}


def summarize_field_extrema(fields: dict[str, list[float] | list[tuple[float, float, float]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for name, values in fields.items():
        flattened: list[float] = []
        for value in values:
            if isinstance(value, tuple):
                flattened.extend(float(component) for component in value)
            else:
                flattened.append(float(value))
        if not flattened:
            summary[name] = {"available": False, "finite": False}
            continue
        summary[name] = {
            "available": True,
            "finite": all(_finite_number(value) for value in flattened),
            "min": min(flattened),
            "max": max(flattened),
        }
    return summary


def write_shock_metrics(config: dict[str, Any], output_dir: Path, profile_rows: list[dict[str, float]] | None = None) -> dict[str, Any]:
    if profile_rows is None:
        raise FileNotFoundError("C08 runtime profile sampling is not available yet; provide profile rows or add field sampling.")
    shock_x = locate_shock_position_from_profile(profile_rows, config["postprocess"]["shock_quantity"])
    windows = average_state_windows(
        profile_rows,
        config["postprocess"]["upstream_window_m"],
        config["postprocess"]["downstream_window_m"],
    )
    jumps = compute_jump_ratios(windows["upstream"], windows["downstream"])
    post_dir = output_dir / "postprocess"
    profile_path = post_dir / "shock_line_samples.csv"
    metrics_path = post_dir / "shock_metrics.json"
    _write_csv(profile_path, PROFILE_COLUMNS, profile_rows)
    metrics = {
        "available": True,
        "shock_position_m": shock_x,
        "upstream": windows["upstream"],
        "downstream": windows["downstream"],
        **jumps,
        "profile_path": str(profile_path),
    }
    post_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics["path"] = str(metrics_path)
    return metrics


def write_conservation_summary(output_dir: Path, mass_error: float | None = None, energy_error: float | None = None) -> dict[str, Any]:
    summary = {
        "available": mass_error is not None and energy_error is not None,
        "mass_conservation_error": mass_error,
        "energy_conservation_proxy": energy_error,
    }
    path = output_dir / "postprocess" / "conservation_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["path"] = str(path)
    return summary
