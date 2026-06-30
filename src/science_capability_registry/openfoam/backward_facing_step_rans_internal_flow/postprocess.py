"""Post-processing for OpenFOAM C03 backward-facing step RANS fields."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import (
    CellGeometry,
    expand_uniform_scalars,
    expand_uniform_vectors,
    finite_values,
    load_cell_geometry,
    load_patch_faces,
    read_internal_scalars,
    read_internal_vectors,
    vector_magnitude,
)

VELOCITY_COLUMNS = ["case_id", "station_x_over_H", "sample_index", "x_m", "y_m", "z_m", "y_over_H", "Ux_m_s", "Uy_m_s", "Uz_m_s", "U_over_Uin"]
SHEAR_COLUMNS = ["case_id", "sample_index", "x_m", "x_over_H", "tau_w_kinematic_m2_s2", "wall_shear_sign", "near_wall_y_m"]
PRESSURE_COLUMNS = ["case_id", "sample_index", "x_m", "x_over_H", "y_m", "p_kinematic_m2_s2", "Cp"]
YPLUS_COLUMNS = ["case_id", "patch", "min_yplus", "mean_yplus", "max_yplus", "sample_count", "method"]


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _nearest_station_cells(cells: list[CellGeometry], target_x: float, tolerance: float) -> list[CellGeometry]:
    distances = [abs(cell.center[0] - target_x) for cell in cells]
    best = min(distances)
    limit = max(best + 1e-12, tolerance)
    return sorted([cell for cell in cells if abs(cell.center[0] - target_x) <= limit], key=lambda cell: cell.center[1])


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pressure_region(cells: list[CellGeometry], pressures: list[float], side: str, width: float) -> float:
    xs = [cell.center[0] for cell in cells]
    if side == "inlet":
        limit = min(xs) + width
        selected = [pressures[cell.index] for cell in cells if cell.center[0] <= limit]
    else:
        limit = max(xs) - width
        selected = [pressures[cell.index] for cell in cells if cell.center[0] >= limit]
    return _mean(selected)


def _field_path(case_dir: Path, time_value: float, name: str) -> Path:
    return case_dir / f"{time_value:g}" / name


def _wall_rows(
    config: dict[str, Any],
    case_dir: Path,
    cells: list[CellGeometry],
    velocities: list[tuple[float, float, float]],
    nut: list[float],
) -> tuple[list[dict[str, Any]], float | None, list[float]]:
    h = float(config["geometry"]["step_height_m"])
    nu = float(config["material"]["kinematic_viscosity_m2_s"])
    rows = []
    yplus_values = []
    downstream = []
    for face in sorted(load_patch_faces(case_dir, "lowerWall"), key=lambda item: item.center[0]):
        cell = cells[face.owner_cell]
        if face.center[0] < -1e-12:
            continue
        dy = max(abs(cell.center[1] - face.center[1]), 1e-12)
        ux = velocities[face.owner_cell][0]
        nu_eff = max(nu + max(nut[face.owner_cell], 0.0), nu)
        tau = nu_eff * ux / dy
        sign = -1 if tau < 0 else 1 if tau > 0 else 0
        yplus = math.sqrt(abs(tau)) * dy / max(nu, 1e-30)
        yplus_values.append(yplus)
        rows.append({
            "case_id": config["case_id"],
            "sample_index": len(rows),
            "x_m": face.center[0],
            "x_over_H": face.center[0] / h,
            "tau_w_kinematic_m2_s2": tau,
            "wall_shear_sign": sign,
            "near_wall_y_m": dy,
        })
        downstream.append((face.center[0] / h, tau))
    reattachment = None
    seen_negative = False
    previous = None
    for x_over_h, tau in downstream:
        if tau < 0:
            seen_negative = True
        if previous is not None and seen_negative:
            prev_x, prev_tau = previous
            if prev_tau <= 0.0 < tau:
                fraction = -prev_tau / max(tau - prev_tau, 1e-30)
                reattachment = prev_x + fraction * (x_over_h - prev_x)
                break
        previous = (x_over_h, tau)
    return rows, reattachment, yplus_values


def _velocity_profile_rows(
    config: dict[str, Any],
    cells: list[CellGeometry],
    velocities: list[tuple[float, float, float]],
) -> list[dict[str, Any]]:
    h = float(config["geometry"]["step_height_m"])
    u_in = float(config["material"]["inlet_velocity_m_s"])
    stations = [float(item) for item in config["postprocess"]["velocity_profile_x_over_H"]]
    tolerance = h * 0.2
    rows = []
    for station in stations:
        target_x = station * h
        station_cells = _nearest_station_cells(cells, target_x, tolerance)
        for sample_index, cell in enumerate(station_cells):
            ux, uy, uz = velocities[cell.index]
            rows.append({
                "case_id": config["case_id"],
                "station_x_over_H": station,
                "sample_index": sample_index,
                "x_m": cell.center[0],
                "y_m": cell.center[1],
                "z_m": cell.center[2],
                "y_over_H": cell.center[1] / h,
                "Ux_m_s": ux,
                "Uy_m_s": uy,
                "Uz_m_s": uz,
                "U_over_Uin": vector_magnitude((ux, uy, uz)) / max(abs(u_in), 1e-30),
            })
    return rows


def _pressure_rows(config: dict[str, Any], cells: list[CellGeometry], pressures: list[float], outlet_pressure: float) -> list[dict[str, Any]]:
    h = float(config["geometry"]["step_height_m"])
    u_in = float(config["material"]["inlet_velocity_m_s"])
    dynamic = max(0.5 * u_in * u_in, 1e-30)
    selected = sorted([cell for cell in cells if abs(cell.center[1]) <= h * 0.65], key=lambda cell: cell.center[0])
    rows = []
    for sample_index, cell in enumerate(selected):
        pressure = pressures[cell.index]
        rows.append({
            "case_id": config["case_id"],
            "sample_index": sample_index,
            "x_m": cell.center[0],
            "x_over_H": cell.center[0] / h,
            "y_m": cell.center[1],
            "p_kinematic_m2_s2": pressure,
            "Cp": (pressure - outlet_pressure) / dynamic,
        })
    return rows


def read_velocity_profile_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_flow_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / "case"
    time_value = float(config["numerics"]["control"]["end_time_iterations"])
    cells = load_cell_geometry(case_dir)
    cell_count = len(cells)
    velocities = expand_uniform_vectors(read_internal_vectors(_field_path(case_dir, time_value, "U")), cell_count)
    pressures = expand_uniform_scalars(read_internal_scalars(_field_path(case_dir, time_value, "p")), cell_count)
    nut_path = _field_path(case_dir, time_value, "nut")
    nut = expand_uniform_scalars(read_internal_scalars(nut_path), cell_count) if nut_path.exists() else [0.0] * cell_count
    speed_values = [vector_magnitude(item) for item in velocities]
    scalar_values = pressures + nut

    h = float(config["geometry"]["step_height_m"])
    inlet_pressure = _pressure_region(cells, pressures, "inlet", h)
    outlet_pressure = _pressure_region(cells, pressures, "outlet", h)
    pressure_drop = abs(inlet_pressure - outlet_pressure)

    velocity_rows = _velocity_profile_rows(config, cells, velocities)
    shear_rows, reattachment, yplus_values = _wall_rows(config, case_dir, cells, velocities, nut)
    pressure_rows = _pressure_rows(config, cells, pressures, outlet_pressure)
    yplus_rows = [{
        "case_id": config["case_id"],
        "patch": "lowerWall",
        "min_yplus": min(yplus_values) if yplus_values else 0.0,
        "mean_yplus": _mean(yplus_values),
        "max_yplus": max(yplus_values) if yplus_values else 0.0,
        "sample_count": len(yplus_values),
        "method": "python near-wall proxy from final U/nut and lowerWall owner cells",
    }]

    post_dir = output_dir / "postprocess"
    velocity_path = post_dir / "velocity_profiles.csv"
    shear_path = post_dir / "lower_wall_shear.csv"
    pressure_path = post_dir / "pressure_coefficient.csv"
    yplus_path = post_dir / "yplus_summary.csv"
    _write_csv(velocity_path, VELOCITY_COLUMNS, velocity_rows)
    _write_csv(shear_path, SHEAR_COLUMNS, shear_rows)
    _write_csv(pressure_path, PRESSURE_COLUMNS, pressure_rows)
    _write_csv(yplus_path, YPLUS_COLUMNS, yplus_rows)

    reverse_count = sum(1 for row in shear_rows if float(row["tau_w_kinematic_m2_s2"]) < 0.0)
    return {
        "time": time_value,
        "cell_count": cell_count,
        "field_stats": {
            "velocity_finite": finite_values(speed_values),
            "pressure_finite": finite_values(pressures),
            "nut_finite": finite_values(nut),
            "max_speed_m_s": max(speed_values) if speed_values else 0.0,
            "min_pressure_kinematic_m2_s2": min(pressures) if pressures else 0.0,
            "max_pressure_kinematic_m2_s2": max(pressures) if pressures else 0.0,
            "scalar_values_finite": finite_values(scalar_values),
        },
        "pressure": {
            "inlet_mean_kinematic_m2_s2": inlet_pressure,
            "outlet_mean_kinematic_m2_s2": outlet_pressure,
            "pressure_drop_kinematic_m2_s2": pressure_drop,
            "coefficient_reference_velocity_m_s": float(config["material"]["inlet_velocity_m_s"]),
        },
        "wall": {
            "sample_count": len(shear_rows),
            "reverse_flow_fraction": reverse_count / len(shear_rows) if shear_rows else 0.0,
            "reattachment_length_over_H": reattachment,
            "min_tau_w_kinematic_m2_s2": min((float(row["tau_w_kinematic_m2_s2"]) for row in shear_rows), default=0.0),
            "max_tau_w_kinematic_m2_s2": max((float(row["tau_w_kinematic_m2_s2"]) for row in shear_rows), default=0.0),
        },
        "profiles": {
            "velocity_profiles": {"path": str(velocity_path), "row_count": len(velocity_rows)},
            "lower_wall_shear": {"path": str(shear_path), "row_count": len(shear_rows)},
            "pressure_coefficient": {"path": str(pressure_path), "row_count": len(pressure_rows)},
            "yplus_summary": {"path": str(yplus_path), "row_count": len(yplus_rows)},
        },
    }
