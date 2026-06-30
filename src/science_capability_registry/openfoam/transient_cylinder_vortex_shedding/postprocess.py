"""Force-coefficient post-processing for OpenFOAM C05."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

FORCE_COLUMNS = ["time_s", "cm", "cd", "cl"]
OPENFOAM_FORCE_COEFFS = "openfoam_forceCoeffs"
PYTHON_PATCH_SURFACE_PROXY = "python_patch_surface_proxy"
VECTOR_RE = re.compile(r"\(([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)")


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


def _list_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\n\s*\d+\s*\(\s*(.*?)\s*\)\s*(?:;)?\s*(?://|\Z)", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Could not parse OpenFOAM list body: {path}")
    return match.group(1)


def _read_points(path: Path) -> list[tuple[float, float, float]]:
    return [tuple(float(value) for value in match.groups()) for match in VECTOR_RE.finditer(_list_body(path))]


def _read_faces(path: Path) -> list[list[int]]:
    faces: list[list[int]] = []
    for line in _list_body(path).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.search(r"(?:\d+)?\(([^()]*)\)", stripped)
        if match:
            faces.append([int(value) for value in match.group(1).split()])
    return faces


def _read_labels(path: Path) -> list[int]:
    return [int(line.strip()) for line in _list_body(path).splitlines() if line.strip()]


def _read_boundary(path: Path) -> dict[str, dict[str, int]]:
    patches: dict[str, dict[str, int]] = {}
    for match in re.finditer(r"(?P<name>[A-Za-z0-9_]+)\s*\{(?P<body>.*?)\}", _list_body(path), flags=re.DOTALL):
        body = match.group("body")
        n_faces = re.search(r"nFaces\s+(\d+);", body)
        start_face = re.search(r"startFace\s+(\d+);", body)
        if n_faces and start_face:
            patches[match.group("name")] = {"nFaces": int(n_faces.group(1)), "startFace": int(start_face.group(1))}
    return patches


def _read_scalar_internal_field(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+\d+\s*\(\s*(.*?)\s*\)\s*;",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not parse nonuniform scalar internalField: {path}")
    return [float(line.strip()) for line in match.group(1).splitlines() if line.strip()]


def _read_vector_internal_field(path: Path) -> list[tuple[float, float, float]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"internalField\s+nonuniform\s+List<vector>\s+\d+\s*\(\s*(.*?)\s*\)\s*;",
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise ValueError(f"Could not parse nonuniform vector internalField: {path}")
    return [tuple(float(value) for value in item.groups()) for item in VECTOR_RE.finditer(match.group(1))]


def _add(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])


def _sub(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _mul(vector: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (vector[0] * scalar, vector[1] * scalar, vector[2] * scalar)


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _magnitude(vector: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _mean(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        raise ValueError("Cannot average an empty point list.")
    scale = 1.0 / len(points)
    return _mul((sum(point[0] for point in points), sum(point[1] for point in points), sum(point[2] for point in points)), scale)


def _face_area_vector(face_points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if len(face_points) < 3:
        return (0.0, 0.0, 0.0)
    origin = face_points[0]
    area = (0.0, 0.0, 0.0)
    for index in range(1, len(face_points) - 1):
        area = _add(area, _cross(_sub(face_points[index], origin), _sub(face_points[index + 1], origin)))
    return _mul(area, 0.5)


def _cell_centers(points: list[tuple[float, float, float]], faces: list[list[int]], owners: list[int], neighbours: list[int]) -> list[tuple[float, float, float]]:
    cell_count = max([*owners, *neighbours], default=-1) + 1
    cell_point_ids: list[set[int]] = [set() for _ in range(cell_count)]
    for face_index, face in enumerate(faces):
        if face_index < len(owners):
            cell_point_ids[owners[face_index]].update(face)
        if face_index < len(neighbours):
            cell_point_ids[neighbours[face_index]].update(face)
    return [_mean([points[point_id] for point_id in sorted(point_ids)]) for point_ids in cell_point_ids]


def _time_directories(case_dir: Path) -> list[tuple[float, Path]]:
    candidates: list[tuple[float, Path]] = []
    for path in case_dir.iterdir():
        if not path.is_dir() or path.name == "0.orig":
            continue
        try:
            time_value = float(path.name)
        except ValueError:
            continue
        if time_value > 0.0 and (path / "p").exists() and (path / "U").exists():
            candidates.append((time_value, path))
    return sorted(candidates, key=lambda item: item[0])


def _patch_force_rows(config: dict[str, Any], output_dir: Path) -> list[dict[str, float]]:
    case_dir = output_dir / "case"
    mesh_dir = case_dir / "constant" / "polyMesh"
    points = _read_points(mesh_dir / "points")
    faces = _read_faces(mesh_dir / "faces")
    owners = _read_labels(mesh_dir / "owner")
    neighbours = _read_labels(mesh_dir / "neighbour")
    boundary = _read_boundary(mesh_dir / "boundary")
    patch_name = config["function_objects"]["force_coefficients"]["patches"][0]
    if patch_name not in boundary:
        raise ValueError(f"OpenFOAM patch {patch_name!r} was not found in polyMesh boundary.")

    centers = _cell_centers(points, faces, owners, neighbours)
    patch = boundary[patch_name]
    patch_faces = range(patch["startFace"], patch["startFace"] + patch["nFaces"])
    rho = float(config["material"]["density_kg_m3"])
    nu = float(config["material"]["kinematic_viscosity_m2_s"])
    mu = rho * nu
    inlet_u = float(config["material"]["inlet_velocity_m_s"])
    diameter = float(config["geometry"]["cylinder_diameter_m"])
    area_ref = diameter * float(config["geometry"]["two_dimensional_thickness_m"])
    coefficient_scale = 0.5 * rho * inlet_u * inlet_u * area_ref
    moment_scale = coefficient_scale * diameter
    center = (float(config["geometry"]["cylinder_center_m"][0]), float(config["geometry"]["cylinder_center_m"][1]), 0.0)
    lift_dir = tuple(float(value) for value in config["function_objects"]["force_coefficients"]["lift_dir"])
    drag_dir = tuple(float(value) for value in config["function_objects"]["force_coefficients"]["drag_dir"])

    rows: list[dict[str, float]] = []
    for time_value, time_dir in _time_directories(case_dir):
        pressure = _read_scalar_internal_field(time_dir / "p")
        velocity = _read_vector_internal_field(time_dir / "U")
        total_force = (0.0, 0.0, 0.0)
        total_moment_z = 0.0
        for face_index in patch_faces:
            face = faces[face_index]
            owner = owners[face_index]
            face_points = [points[point_id] for point_id in face]
            face_center = _mean(face_points)
            area_vector = _face_area_vector(face_points)
            if _dot(area_vector, _sub(face_center, centers[owner])) < 0.0:
                area_vector = _mul(area_vector, -1.0)
            area = _magnitude(area_vector)
            if area <= 0.0:
                continue
            normal = _mul(area_vector, 1.0 / area)
            owner_velocity = velocity[owner]
            normal_velocity = _mul(normal, _dot(owner_velocity, normal))
            tangential_velocity = _sub(owner_velocity, normal_velocity)
            wall_distance = abs(_dot(_sub(face_center, centers[owner]), normal))
            viscous_force = (0.0, 0.0, 0.0)
            if wall_distance > 0.0 and mu > 0.0:
                viscous_force = _mul(tangential_velocity, mu * area / wall_distance)
            pressure_force = _mul(area_vector, rho * pressure[owner])
            face_force = _add(pressure_force, viscous_force)
            total_force = _add(total_force, face_force)
            arm = _sub(face_center, center)
            total_moment_z += _cross(arm, face_force)[2]
        rows.append(
            {
                "time_s": time_value,
                "cm": total_moment_z / moment_scale if moment_scale > 0.0 else math.nan,
                "cd": _dot(total_force, drag_dir) / coefficient_scale if coefficient_scale > 0.0 else math.nan,
                "cl": _dot(total_force, lift_dir) / coefficient_scale if coefficient_scale > 0.0 else math.nan,
            }
        )
    return rows


def _write_openfoam_force_coefficients(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
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
    force_info.update({"source": OPENFOAM_FORCE_COEFFS, "input_path": str(candidates[-1])})
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


def _write_python_patch_force_proxy(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    rows = _patch_force_rows(config, output_dir)
    force_info = write_force_coefficients_csv(rows, output_dir / "postprocess" / "force_coefficients.csv")
    force_info.update(
        {
            "source": PYTHON_PATCH_SURFACE_PROXY,
            "method": "pressure plus first-cell tangential viscous proxy integrated on the configured wall patch",
            "patch": config["function_objects"]["force_coefficients"]["patches"][0],
            "source_paths": {
                "mesh": str(output_dir / "case" / "constant" / "polyMesh"),
                "fields": str(output_dir / "case" / "<time>" / "{p,U}"),
            },
        }
    )
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


def write_force_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    source = config["postprocess"].get("force_extraction_source", OPENFOAM_FORCE_COEFFS)
    if source == OPENFOAM_FORCE_COEFFS:
        return _write_openfoam_force_coefficients(config, output_dir)
    if source == PYTHON_PATCH_SURFACE_PROXY:
        return _write_python_patch_force_proxy(config, output_dir)
    return {
        "force_coefficients": {"available": False, "reason": f"Unsupported force extraction source: {source}"},
        "strouhal": {"available": False, "reason": "force coefficient time series missing"},
    }
