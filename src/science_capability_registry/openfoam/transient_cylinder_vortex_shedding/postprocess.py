"""Force-coefficient post-processing for OpenFOAM C05."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

FORCE_COLUMNS = ["time_s", "cm", "cd", "cl"]


def read_force_coefficients(path: str | Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 4:
                continue
            rows.append(
                {
                    "time_s": float(parts[0]),
                    "cm": float(parts[1]),
                    "cd": float(parts[2]),
                    "cl": float(parts[3]),
                }
            )
    return rows


def write_force_coefficients_csv(rows: list[dict[str, float]], path: str | Path) -> dict[str, Any]:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORCE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in FORCE_COLUMNS})
    return {
        "available": bool(rows),
        "path": str(output_path),
        "row_count": len(rows),
    }


def estimate_strouhal(rows: list[dict[str, float]], cylinder_diameter_m: float, inlet_velocity_m_s: float) -> dict[str, Any]:
    if len(rows) < 5:
        return {"available": False, "reason": "at least five force samples are required"}
    peaks: list[dict[str, float]] = []
    for index in range(1, len(rows) - 1):
        previous_cl = rows[index - 1]["cl"]
        current_cl = rows[index]["cl"]
        next_cl = rows[index + 1]["cl"]
        if current_cl > previous_cl and current_cl >= next_cl:
            peaks.append(rows[index])
    if len(peaks) < 3:
        return {"available": False, "reason": "at least three lift peaks are required", "peak_count": len(peaks)}
    periods = [peaks[index + 1]["time_s"] - peaks[index]["time_s"] for index in range(len(peaks) - 1)]
    finite_periods = [period for period in periods if math.isfinite(period) and period > 0.0]
    if not finite_periods:
        return {"available": False, "reason": "no positive finite lift-peak periods were found", "peak_count": len(peaks)}
    mean_period = sum(finite_periods) / len(finite_periods)
    frequency_hz = 1.0 / mean_period
    strouhal = frequency_hz * cylinder_diameter_m / inlet_velocity_m_s
    return {
        "available": True,
        "peak_count": len(peaks),
        "mean_period_s": mean_period,
        "frequency_hz": frequency_hz,
        "strouhal_number": strouhal,
    }


def write_strouhal_summary(summary: dict[str, Any], path: str | Path) -> dict[str, Any]:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {**summary, "path": str(output_path)}


def write_force_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / "case"
    candidates = sorted(
        {
            *case_dir.glob("postProcessing/forceCoeffs*/**/coefficient.dat"),
            *case_dir.glob("processor*/postProcessing/forceCoeffs*/**/coefficient.dat"),
        }
    )
    if not candidates:
        return {
            "force_coefficients": {"available": False, "reason": "OpenFOAM coefficient.dat was not found"},
            "strouhal": {"available": False, "reason": "force coefficient time series missing"},
        }
    rows = read_force_coefficients(candidates[-1])
    force_info = write_force_coefficients_csv(rows, output_dir / "postprocess" / "force_coefficients.csv")
    strouhal = estimate_strouhal(
        rows,
        cylinder_diameter_m=float(config["geometry"]["cylinder_diameter_m"]),
        inlet_velocity_m_s=float(config["material"]["inlet_velocity_m_s"]),
    )
    strouhal = write_strouhal_summary(strouhal, output_dir / "postprocess" / "strouhal_summary.json")
    return {
        "force_coefficients": force_info,
        "strouhal": strouhal,
    }
