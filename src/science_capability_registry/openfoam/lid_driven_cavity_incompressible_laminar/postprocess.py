"""Post-processing helpers for OpenFOAM C01."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
VECTOR_RE = re.compile(rf"\(\s*({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*\)")
PROFILE_COLUMNS = [
    "case_id",
    "line_id",
    "time_s",
    "sample_index",
    "x_m",
    "y_m",
    "z_m",
    "x_over_L",
    "y_over_L",
    "Ux_m_s",
    "Uy_m_s",
    "Uz_m_s",
    "U_mag_m_s",
]


def _read_internal_vectors(path: Path) -> list[tuple[float, float, float]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = re.search(r"internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\(", text)
    if marker is None:
        raise ValueError(f"Could not locate nonuniform vector internalField in {path}")
    count = int(marker.group(1))
    vectors: list[tuple[float, float, float]] = []
    for match in VECTOR_RE.finditer(text[marker.end() :]):
        vectors.append((float(match.group(1)), float(match.group(2)), float(match.group(3))))
        if len(vectors) == count:
            break
    if len(vectors) != count:
        raise ValueError(f"Expected {count} vectors in {path}, found {len(vectors)}")
    return vectors


def _interpolate_vector(
    coords: list[float],
    values: list[tuple[float, float, float]],
    target: float,
) -> tuple[float, float, float]:
    if target <= coords[0]:
        return values[0]
    if target >= coords[-1]:
        return values[-1]
    for index in range(len(coords) - 1):
        left = coords[index]
        right = coords[index + 1]
        if left <= target <= right:
            weight = (target - left) / (right - left)
            return tuple(
                values[index][component] * (1.0 - weight)
                + values[index + 1][component] * weight
                for component in range(3)
            )
    return values[-1]


def _component_range(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def _max_abs_gradient(coords: list[float], values: list[float]) -> float:
    gradients = []
    for index in range(len(values) - 1):
        delta_coord = coords[index + 1] - coords[index]
        if delta_coord:
            gradients.append(abs((values[index + 1] - values[index]) / delta_coord))
    return max(gradients, default=0.0)


def _row(
    case_id: str,
    line_id: str,
    time_s: float,
    sample_index: int,
    x_m: float,
    y_m: float,
    z_m: float,
    side: float,
    velocity: tuple[float, float, float],
) -> dict[str, float | int | str]:
    ux, uy, uz = velocity
    return {
        "case_id": case_id,
        "line_id": line_id,
        "time_s": time_s,
        "sample_index": sample_index,
        "x_m": x_m,
        "y_m": y_m,
        "z_m": z_m,
        "x_over_L": x_m / side,
        "y_over_L": y_m / side,
        "Ux_m_s": ux,
        "Uy_m_s": uy,
        "Uz_m_s": uz,
        "U_mag_m_s": math.sqrt(ux * ux + uy * uy + uz * uz),
    }


def _write_profile_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_profile_csv(path: str | Path) -> list[dict[str, float | int | str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "case_id": row["case_id"],
                    "line_id": row["line_id"],
                    "time_s": float(row["time_s"]),
                    "sample_index": int(row["sample_index"]),
                    "x_m": float(row["x_m"]),
                    "y_m": float(row["y_m"]),
                    "z_m": float(row["z_m"]),
                    "x_over_L": float(row["x_over_L"]),
                    "y_over_L": float(row["y_over_L"]),
                    "Ux_m_s": float(row["Ux_m_s"]),
                    "Uy_m_s": float(row["Uy_m_s"]),
                    "Uz_m_s": float(row["Uz_m_s"]),
                    "U_mag_m_s": float(row["U_mag_m_s"]),
                }
            )
        return rows


def _finite_rows(rows: list[dict[str, float | int | str]]) -> bool:
    numeric_keys = [key for key in PROFILE_COLUMNS if key not in {"case_id", "line_id"}]
    for row in rows:
        for key in numeric_keys:
            if not math.isfinite(float(row[key])):
                return False
    return True


def _monotonic(rows: list[dict[str, float | int | str]], key: str) -> bool:
    values = [float(row[key]) for row in rows]
    return all(left <= right for left, right in zip(values, values[1:]))


def _profile_stats(
    rows: list[dict[str, float | int | str]],
    component: str,
    coord: str,
) -> dict[str, float | int | bool]:
    values = [float(row[component]) for row in rows]
    coords = [float(row[coord]) for row in rows]
    return {
        "row_count": len(rows),
        "finite": _finite_rows(rows),
        "coordinate_monotonic": _monotonic(rows, coord),
        f"{component}_min": min(values) if values else 0.0,
        f"{component}_max": max(values) if values else 0.0,
        f"{component}_range": _component_range(values),
        f"max_abs_d{component}_d{coord}": _max_abs_gradient(coords, values),
    }


def write_centerline_profiles(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    cells = config["mesh"]["cells"]
    nx = int(cells[0])
    ny = int(cells[1])
    side = float(config["geometry"]["cavity_side_length_m"])
    z_m = float(config["geometry"].get("thickness_m", side * 0.1)) / 2.0
    time_s = float(config["numerics"]["control"]["end_time_s"])
    final_dir = output_dir / "case" / f"{time_s:g}"
    field_path = final_dir / "U"
    vectors = _read_internal_vectors(field_path)
    expected = nx * ny
    if len(vectors) != expected:
        raise ValueError(f"Expected {expected} cell vectors, found {len(vectors)}")

    xs = [(index + 0.5) * side / nx for index in range(nx)]
    ys = [(index + 0.5) * side / ny for index in range(ny)]
    target = side / 2.0

    vertical_rows: list[dict[str, float | int | str]] = []
    for sample_index in range(ny + 1):
        y_m = sample_index * side / ny
        if sample_index == 0:
            velocity = (0.0, 0.0, 0.0)
        elif sample_index == ny:
            velocity = (float(config["material"]["lid_velocity_m_s"]), 0.0, 0.0)
        else:
            row_vectors = [vectors[(sample_index - 1) * nx + i] for i in range(nx)]
            velocity = _interpolate_vector(xs, row_vectors, target)
        vertical_rows.append(_row(config["case_id"], "vertical_centerline_Ux", time_s, sample_index, target, y_m, z_m, side, velocity))

    horizontal_rows: list[dict[str, float | int | str]] = []
    for sample_index in range(nx + 1):
        x_m = sample_index * side / nx
        if sample_index == 0 or sample_index == nx:
            velocity = (0.0, 0.0, 0.0)
        else:
            column_vectors = [vectors[j * nx + sample_index - 1] for j in range(ny)]
            velocity = _interpolate_vector(ys, column_vectors, target)
        horizontal_rows.append(_row(config["case_id"], "horizontal_centerline_Uy", time_s, sample_index, x_m, target, z_m, side, velocity))

    postprocess_dir = output_dir / "postprocess"
    vertical_path = postprocess_dir / "centerline_vertical_Ux.csv"
    horizontal_path = postprocess_dir / "centerline_horizontal_Uy.csv"
    _write_profile_csv(vertical_path, vertical_rows)
    _write_profile_csv(horizontal_path, horizontal_rows)

    max_speed = max(math.sqrt(ux * ux + uy * uy + uz * uz) for ux, uy, uz in vectors)
    return {
        "profiles": {
            "vertical_centerline_Ux": {
                "path": str(vertical_path),
                "line_id": "vertical_centerline_Ux",
                "time_s": time_s,
                "sample_count": len(vertical_rows),
                "target": "x = L/2",
                "primary_component": "Ux_m_s",
                "stats": _profile_stats(vertical_rows, "Ux_m_s", "y_m"),
            },
            "horizontal_centerline_Uy": {
                "path": str(horizontal_path),
                "line_id": "horizontal_centerline_Uy",
                "time_s": time_s,
                "sample_count": len(horizontal_rows),
                "target": "y = L/2",
                "primary_component": "Uy_m_s",
                "stats": _profile_stats(horizontal_rows, "Uy_m_s", "x_m"),
            },
        },
        "field_stats": {
            "cell_count": len(vectors),
            "max_speed_m_s": max_speed,
        },
    }
