"""Post-processing helpers for C04 motorBike force and y+ metrics."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

FORCE_COLUMNS = ["iteration", "cm", "cd", "cl"]
YPLUS_COLUMNS = ["patch", "sample_count", "min", "max", "mean"]


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
                    "iteration": float(parts[0]),
                    "cm": float(parts[1]),
                    "cd": float(parts[2]),
                    "cl": float(parts[3]),
                }
            )
    return rows


def _finite_rows(rows: list[dict[str, float]], columns: list[str]) -> list[dict[str, float]]:
    return [row for row in rows if all(math.isfinite(float(row[column])) for column in columns)]


def _mean(values: list[float]) -> float:
    if not values:
        return math.nan
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if not values:
        return math.nan
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def summarize_force_tail(rows: list[dict[str, float]], tail_window_iterations: int) -> dict[str, Any]:
    finite = _finite_rows(rows, FORCE_COLUMNS)
    selected = finite[-tail_window_iterations:] if tail_window_iterations > 0 else finite
    cds = [float(row["cd"]) for row in selected]
    cls = [float(row["cl"]) for row in selected]
    return {
        "available": bool(selected),
        "row_count": len(rows),
        "finite_row_count": len(finite),
        "tail_row_count": len(selected),
        "cd_tail_mean": _mean(cds),
        "cd_tail_std": _std(cds),
        "cl_tail_mean": _mean(cls),
        "cl_tail_std": _std(cls),
    }


def write_force_coefficients_csv(rows: list[dict[str, float]], path: str | Path) -> dict[str, Any]:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORCE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in FORCE_COLUMNS})
    return {"available": bool(rows), "path": str(output_path), "row_count": len(rows)}


def summarize_y_plus(rows: list[dict[str, float]]) -> dict[str, Any]:
    finite = _finite_rows(rows, ["min", "max", "mean"])
    sample_count = sum(int(row.get("sample_count", 0)) for row in rows)
    mins = [float(row["min"]) for row in finite]
    maxs = [float(row["max"]) for row in finite]
    means = [float(row["mean"]) for row in finite]
    return {
        "available": bool(finite),
        "patch_count": len(rows),
        "sample_count": sample_count,
        "finite_patch_count": len(finite),
        "min": min(mins) if mins else math.nan,
        "max": max(maxs) if maxs else math.nan,
        "mean": _mean(means),
    }


def write_y_plus_summary(rows: list[dict[str, float]], path: str | Path) -> dict[str, Any]:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=YPLUS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in YPLUS_COLUMNS})
    summary = summarize_y_plus(rows)
    summary["path"] = str(output_path)
    return summary


def write_force_metrics(config: dict[str, Any], output_dir: Path, rows: list[dict[str, float]] | None = None) -> dict[str, Any]:
    if rows is None:
        case_dir = output_dir / "case"
        candidates = sorted(
            {
                *case_dir.glob("postProcessing/forceCoeffs*/**/coefficient.dat"),
                *case_dir.glob("processor*/postProcessing/forceCoeffs*/**/coefficient.dat"),
            }
        )
        if not candidates:
            return {"available": False, "reason": "OpenFOAM forceCoeffs coefficient.dat was not found"}
        rows = read_force_coefficients(candidates[-1])
    csv_info = write_force_coefficients_csv(rows, output_dir / "postprocess" / "force_coefficients.csv")
    summary = summarize_force_tail(rows, int(config["postprocess"]["force_tail_window_iterations"]))
    metrics = {**csv_info, **summary, "source": config["postprocess"]["force_extraction_source"]}
    summary_path = output_dir / "postprocess" / "force_coefficients_summary.json"
    summary_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics["summary_path"] = str(summary_path)
    return metrics
