"""Analytical post-processing for OpenFOAM C02 potential-flow cylinder."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import (
    expand_uniform_scalars,
    expand_uniform_vectors,
    finite_values,
    load_cell_geometry,
    load_patch_faces,
    read_internal_scalars,
    read_internal_vectors,
    vector_magnitude,
)

FIELD_COLUMNS = [
    "cell_index",
    "x_m",
    "y_m",
    "r_m",
    "theta_rad",
    "Ux_m_s",
    "Uy_m_s",
    "Ux_ref_m_s",
    "Uy_ref_m_s",
    "velocity_error_m_s",
    "p_kinematic_m2_s2",
    "p_ref_kinematic_m2_s2",
    "pressure_error_m2_s2",
]
CP_COLUMNS = [
    "face_index",
    "owner_cell",
    "x_m",
    "y_m",
    "theta_rad",
    "cp",
    "cp_ref",
    "cp_error",
]


def analytical_velocity(
    x_m: float,
    y_m: float,
    radius_m: float,
    inlet_velocity_m_s: float,
) -> tuple[float, float, float]:
    r2 = x_m * x_m + y_m * y_m
    if r2 <= 0.0:
        return (math.nan, math.nan, 0.0)
    theta = math.atan2(y_m, x_m)
    ratio = radius_m * radius_m / r2
    return (
        inlet_velocity_m_s * (1.0 - ratio * math.cos(2.0 * theta)),
        -inlet_velocity_m_s * ratio * math.sin(2.0 * theta),
        0.0,
    )


def analytical_pressure_kinematic(
    velocity_ref: tuple[float, float, float],
    inlet_velocity_m_s: float,
    p_reference_kinematic_m2_s2: float,
) -> float:
    speed2 = sum(component * component for component in velocity_ref)
    return p_reference_kinematic_m2_s2 + 0.5 * (inlet_velocity_m_s * inlet_velocity_m_s - speed2)


def analytical_surface_cp(theta_rad: float) -> float:
    return 1.0 - 4.0 * math.sin(theta_rad) * math.sin(theta_rad)


def _l2(values: list[float]) -> float | None:
    if not values:
        return None
    return math.sqrt(sum(value * value for value in values) / len(values))


def _linf(values: list[float]) -> float | None:
    if not values:
        return None
    return max(abs(value) for value in values)


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _latest_field_dir(case_dir: Path) -> Path | None:
    candidates: list[tuple[float, Path]] = []
    for path in case_dir.iterdir():
        if not path.is_dir() or path.name == "0.orig":
            continue
        try:
            value = float(path.name)
        except ValueError:
            continue
        if (path / "U").exists() and (path / "p").exists():
            candidates.append((value, path))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _field_rows(config: dict[str, Any], output_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    case_dir = output_dir / "case"
    field_dir = _latest_field_dir(case_dir)
    if field_dir is None:
        return [], {"available": False, "reason": "No solved U/p time directory found."}

    cells = load_cell_geometry(case_dir)
    velocities = expand_uniform_vectors(read_internal_vectors(field_dir / "U"), len(cells))
    pressures = expand_uniform_scalars(read_internal_scalars(field_dir / "p"), len(cells))
    radius = float(config["geometry"]["cylinder_radius_m"])
    inlet_u = float(config["material"]["inlet_velocity_m_s"])
    p_ref = float(config["material"]["p_reference_kinematic_m2_s2"])
    center = config["geometry"]["cylinder_center_m"]
    cx = float(center[0])
    cy = float(center[1])
    exclude_radius = radius * float(config["analytical_reference"]["exclude_radius_factor"])
    domain_half_width = float(config["geometry"]["domain_half_width_m"])
    boundary_buffer = float(config["analytical_reference"]["boundary_buffer_m"])

    rows = []
    velocity_errors = []
    pressure_errors = []
    for cell, velocity, pressure in zip(cells, velocities, pressures):
        x = cell.center[0] - cx
        y = cell.center[1] - cy
        r = math.sqrt(x * x + y * y)
        if r <= exclude_radius:
            continue
        if abs(cell.center[0]) >= domain_half_width - boundary_buffer:
            continue
        if abs(cell.center[1]) >= domain_half_width - boundary_buffer:
            continue
        velocity_ref = analytical_velocity(x, y, radius, inlet_u)
        pressure_ref = analytical_pressure_kinematic(velocity_ref, inlet_u, p_ref)
        velocity_error = vector_magnitude(
            (
                velocity[0] - velocity_ref[0],
                velocity[1] - velocity_ref[1],
                velocity[2] - velocity_ref[2],
            )
        )
        pressure_error = float(pressure) - pressure_ref
        velocity_errors.append(velocity_error)
        pressure_errors.append(pressure_error)
        rows.append(
            {
                "cell_index": cell.index,
                "x_m": cell.center[0],
                "y_m": cell.center[1],
                "r_m": r,
                "theta_rad": math.atan2(y, x),
                "Ux_m_s": velocity[0],
                "Uy_m_s": velocity[1],
                "Ux_ref_m_s": velocity_ref[0],
                "Uy_ref_m_s": velocity_ref[1],
                "velocity_error_m_s": velocity_error,
                "p_kinematic_m2_s2": pressure,
                "p_ref_kinematic_m2_s2": pressure_ref,
                "pressure_error_m2_s2": pressure_error,
            }
        )
    summary = {
        "available": bool(rows),
        "sample_count": len(rows),
        "velocity_l2_error": _l2(velocity_errors),
        "velocity_linf_error": _linf(velocity_errors),
        "pressure_l2_error": _l2(pressure_errors),
        "pressure_linf_error": _linf(pressure_errors),
        "field_dir": str(field_dir),
    }
    return rows, summary


def _surface_cp_rows(config: dict[str, Any], output_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    case_dir = output_dir / "case"
    field_dir = _latest_field_dir(case_dir)
    if field_dir is None:
        return [], {"available": False, "reason": "No solved p time directory found."}
    cells = load_cell_geometry(case_dir)
    pressures = expand_uniform_scalars(read_internal_scalars(field_dir / "p"), len(cells))
    faces = load_patch_faces(case_dir, config["postprocess"]["surface_patch"])
    inlet_u = float(config["material"]["inlet_velocity_m_s"])
    p_ref = float(config["material"]["p_reference_kinematic_m2_s2"])
    center = config["geometry"]["cylinder_center_m"]
    cx = float(center[0])
    cy = float(center[1])
    denom = 0.5 * inlet_u * inlet_u
    rows = []
    errors = []
    for face in faces:
        x = face.center[0] - cx
        y = face.center[1] - cy
        theta = math.atan2(y, x)
        cp = (pressures[face.owner_cell] - p_ref) / denom if denom > 0.0 else math.nan
        cp_ref = analytical_surface_cp(theta)
        error = cp - cp_ref
        rows.append(
            {
                "face_index": face.face_index,
                "owner_cell": face.owner_cell,
                "x_m": face.center[0],
                "y_m": face.center[1],
                "theta_rad": theta,
                "cp": cp,
                "cp_ref": cp_ref,
                "cp_error": error,
            }
        )
        errors.append(error)
    summary = {
        "available": bool(rows),
        "sample_count": len(rows),
        "cp_l2_error": _l2(errors),
        "cp_linf_error": _linf(errors),
        "field_dir": str(field_dir),
    }
    return rows, summary


def write_analytical_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    field_rows, field_summary = _field_rows(config, output_dir)
    cp_rows, cp_summary = _surface_cp_rows(config, output_dir)
    postprocess_dir = output_dir / "postprocess"
    field_path = postprocess_dir / "field_analytical_comparison.csv"
    cp_path = postprocess_dir / "cylinder_cp_comparison.csv"
    summary_path = postprocess_dir / "analytical_error_summary.json"

    if field_rows:
        _write_csv(field_path, field_rows, FIELD_COLUMNS)
    if cp_rows:
        _write_csv(cp_path, cp_rows, CP_COLUMNS)
    summary = {
        "field": {**field_summary, "path": str(field_path) if field_rows else ""},
        "surface_cp": {**cp_summary, "path": str(cp_path) if cp_rows else ""},
        "finite": finite_values(
            [
                value
                for value in [
                    field_summary.get("velocity_l2_error"),
                    field_summary.get("velocity_linf_error"),
                    field_summary.get("pressure_l2_error"),
                    cp_summary.get("cp_linf_error"),
                ]
                if value is not None
            ]
        ),
        "reference": config["analytical_reference"],
    }
    postprocess_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["path"] = str(summary_path)
    return summary
