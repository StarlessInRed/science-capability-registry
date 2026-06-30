"""Post-processing for OpenFOAM C06 dam-break VOF fields."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import CellGeometry, expand_uniform_scalars, finite_values, load_cell_geometry, read_internal_scalars

FRONT_COLUMNS = ["case_id", "time_s", "front_x_m", "front_y_m", "alpha_threshold", "wet_cell_count"]
VOLUME_COLUMNS = ["case_id", "time_s", "water_volume_m3", "relative_error"]
BOUNDS_COLUMNS = ["case_id", "time_s", "alpha_min", "alpha_max", "below_zero_count", "above_one_count"]
GAUGE_COLUMNS = ["case_id", "gauge_id", "time_s", "x_m", "z_m", "interface_height_m"]
SURFACE_COLUMNS = ["case_id", "time_s", "point_index", "x_m", "y_m", "z_m", "alpha_threshold"]


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _time_dirs(case_dir: Path) -> list[tuple[float, Path]]:
    dirs = []
    for path in case_dir.iterdir():
        if not path.is_dir():
            continue
        try:
            value = float(path.name)
        except ValueError:
            continue
        if (path / "alpha.water").exists():
            dirs.append((value, path))
    dirs.sort(key=lambda item: item[0])
    return dirs


def _nearest_x_cells(cells: list[CellGeometry], target_x: float) -> list[CellGeometry]:
    best = min(abs(cell.center[0] - target_x) for cell in cells)
    return [cell for cell in cells if abs(cell.center[0] - target_x) <= best + 1e-12]


def _front(alpha: list[float], cells: list[CellGeometry], threshold: float) -> tuple[float, float, int]:
    wet = [cell for cell in cells if alpha[cell.index] >= threshold]
    if not wet:
        return 0.0, 0.0, 0
    front_cell = max(wet, key=lambda cell: cell.center[0])
    return front_cell.center[0], front_cell.center[1], len(wet)


def _gauge_height(alpha: list[float], cells: list[CellGeometry], x_m: float, threshold: float) -> float:
    selected = _nearest_x_cells(cells, x_m)
    wet_y = [cell.center[1] for cell in selected if alpha[cell.index] >= threshold]
    return max(wet_y) if wet_y else 0.0


def _surface_profile(alpha: list[float], cells: list[CellGeometry], threshold: float, case_id: str, time_s: float) -> list[dict[str, Any]]:
    bins: dict[float, CellGeometry] = {}
    for cell in cells:
        if alpha[cell.index] < threshold:
            continue
        key = round(cell.center[0], 5)
        current = bins.get(key)
        if current is None or cell.center[1] > current.center[1]:
            bins[key] = cell
    rows = []
    for index, cell in enumerate(sorted(bins.values(), key=lambda item: item.center[0])):
        rows.append({"case_id": case_id, "time_s": time_s, "point_index": index, "x_m": cell.center[0], "y_m": cell.center[1], "z_m": cell.center[2], "alpha_threshold": threshold})
    return rows


def read_front_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_vof_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / "case"
    cells = load_cell_geometry(case_dir)
    threshold = float(config["postprocess"]["alpha_threshold"])
    gauges = [float(item) for item in config["postprocess"]["gauge_x_m"]]
    front_rows: list[dict[str, Any]] = []
    volume_rows: list[dict[str, Any]] = []
    bounds_rows: list[dict[str, Any]] = []
    gauge_rows: list[dict[str, Any]] = []
    surface_rows: list[dict[str, Any]] = []
    initial_volume = None
    latest_alpha: list[float] = []
    latest_time = 0.0
    for time_s, time_dir in _time_dirs(case_dir):
        alpha = expand_uniform_scalars(read_internal_scalars(time_dir / "alpha.water"), len(cells))
        latest_alpha = alpha
        latest_time = time_s
        water_volume = sum(max(0.0, min(1.0, alpha[cell.index])) * cell.volume for cell in cells)
        if initial_volume is None:
            initial_volume = water_volume
        rel_error = 0.0 if not initial_volume else (water_volume - initial_volume) / initial_volume
        front_x, front_y, wet_count = _front(alpha, cells, threshold)
        front_rows.append({"case_id": config["case_id"], "time_s": time_s, "front_x_m": front_x, "front_y_m": front_y, "alpha_threshold": threshold, "wet_cell_count": wet_count})
        volume_rows.append({"case_id": config["case_id"], "time_s": time_s, "water_volume_m3": water_volume, "relative_error": rel_error})
        bounds_rows.append({"case_id": config["case_id"], "time_s": time_s, "alpha_min": min(alpha), "alpha_max": max(alpha), "below_zero_count": sum(1 for value in alpha if value < -1e-12), "above_one_count": sum(1 for value in alpha if value > 1.0 + 1e-12)})
        for gauge_index, x_m in enumerate(gauges):
            gauge_rows.append({"case_id": config["case_id"], "gauge_id": f"g{gauge_index}", "time_s": time_s, "x_m": x_m, "z_m": 0.0, "interface_height_m": _gauge_height(alpha, cells, x_m, threshold)})
    if latest_alpha:
        surface_rows = _surface_profile(latest_alpha, cells, threshold, config["case_id"], latest_time)

    post_dir = output_dir / "postprocess"
    front_path = post_dir / "front_position_history.csv"
    volume_path = post_dir / "water_volume_history.csv"
    bounds_path = post_dir / "alpha_bounds_history.csv"
    gauge_path = post_dir / "gauge_interface_height_history.csv"
    surface_path = post_dir / "free_surface_profile_final.csv"
    _write_csv(front_path, FRONT_COLUMNS, front_rows)
    _write_csv(volume_path, VOLUME_COLUMNS, volume_rows)
    _write_csv(bounds_path, BOUNDS_COLUMNS, bounds_rows)
    _write_csv(gauge_path, GAUGE_COLUMNS, gauge_rows)
    _write_csv(surface_path, SURFACE_COLUMNS, surface_rows)

    final_front = front_rows[-1] if front_rows else {}
    final_volume = volume_rows[-1] if volume_rows else {}
    final_bounds = bounds_rows[-1] if bounds_rows else {}
    return {
        "time_history_count": len(front_rows),
        "cell_count": len(cells),
        "alpha_finite": finite_values(latest_alpha),
        "front": final_front,
        "volume": final_volume,
        "alpha_bounds": final_bounds,
        "profiles": {
            "front_position_history": {"path": str(front_path), "row_count": len(front_rows)},
            "water_volume_history": {"path": str(volume_path), "row_count": len(volume_rows)},
            "alpha_bounds_history": {"path": str(bounds_path), "row_count": len(bounds_rows)},
            "gauge_interface_height_history": {"path": str(gauge_path), "row_count": len(gauge_rows)},
            "free_surface_profile_final": {"path": str(surface_path), "row_count": len(surface_rows)},
        },
    }
