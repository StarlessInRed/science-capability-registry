"""Post-processing helpers for C08 shock metrics."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import (
    CellGeometry,
    expand_uniform_scalars,
    expand_uniform_vectors,
    load_cell_geometry,
    read_boundary,
    read_faces,
    read_internal_scalars,
    read_internal_vectors,
    read_label_list,
    read_points,
)

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


def locate_shock_position_from_profile(
    rows: list[dict[str, float]],
    quantity: str = "p",
    search_window_m: tuple[float, float] | list[float] | None = None,
) -> float:
    ordered = sorted(rows, key=lambda row: float(row["x_m"]))
    if search_window_m is not None:
        search_start, search_stop = float(search_window_m[0]), float(search_window_m[1])
        if search_start >= search_stop:
            raise ValueError("Shock search window must have increasing bounds.")
        ordered = [row for row in ordered if search_start <= float(row["x_m"]) <= search_stop]
    if len(ordered) < 2:
        raise ValueError("At least two profile samples are required to locate a shock.")
    gradients: list[tuple[float, float]] = []
    for left, right in zip(ordered, ordered[1:]):
        dx = float(right["x_m"]) - float(left["x_m"])
        if dx <= 0.0:
            continue
        gradient = (float(right[quantity]) - float(left[quantity])) / dx
        if gradient <= 0.0:
            continue
        gradients.append(((float(left["x_m"]) + float(right["x_m"])) / 2.0, gradient))
    if not gradients:
        raise ValueError("No positive shock-candidate gradient was found in the configured search window.")
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


def _numeric_time(path: Path) -> float | None:
    try:
        return float(path.name)
    except ValueError:
        return None


def _latest_time_dir(case_dir: Path) -> Path:
    candidates = []
    for path in case_dir.iterdir():
        if not path.is_dir():
            continue
        time_value = _numeric_time(path)
        if time_value is not None and (path / "p").exists() and (path / "T").exists() and (path / "U").exists():
            candidates.append((time_value, path))
    if not candidates:
        raise FileNotFoundError(f"No solved OpenFOAM time directories found under {case_dir}")
    return max(candidates, key=lambda item: item[0])[1]


def _read_case_fields(case_dir: Path, time_dir: Path) -> dict[str, list[float] | list[tuple[float, float, float]]]:
    cells = load_cell_geometry(case_dir)
    fields: dict[str, list[float] | list[tuple[float, float, float]]] = {
        "p": expand_uniform_scalars(read_internal_scalars(time_dir / "p"), len(cells)),
        "T": expand_uniform_scalars(read_internal_scalars(time_dir / "T"), len(cells)),
        "U": expand_uniform_vectors(read_internal_vectors(time_dir / "U"), len(cells)),
    }
    rho_path = time_dir / "rho"
    if rho_path.exists():
        fields["rho"] = expand_uniform_scalars(read_internal_scalars(rho_path), len(cells))
    return fields


def _rho_from_pressure_temperature(p_values: list[float], t_values: list[float], gamma: float) -> list[float]:
    if gamma <= 1.0:
        raise ValueError("Specific heat ratio gamma must be greater than one.")
    rho_values = []
    for pressure, temperature in zip(p_values, t_values):
        if temperature <= 0.0:
            raise ValueError("Temperature must be positive when deriving density.")
        rho_values.append(gamma * pressure / temperature)
    return rho_values


def _configured_sample_line(config: dict[str, Any]) -> dict[str, Any]:
    lines = config.get("postprocess", {}).get("sample_lines", [])
    if not lines:
        raise ValueError("C08 postprocess.sample_lines must contain at least one line.")
    line = lines[0]
    if line.get("axis") != "x":
        raise NotImplementedError("C08 runtime field sampling currently supports x-axis sample lines only.")
    return line


def select_x_axis_profile_rows(
    cells: list[CellGeometry],
    p_values: list[float],
    rho_values: list[float],
    t_values: list[float],
    u_values: list[tuple[float, float, float]],
    fixed_y_m: float,
) -> list[dict[str, float]]:
    selected_by_x: dict[float, tuple[float, int]] = {}
    for cell in cells:
        x_key = round(float(cell.center[0]), 9)
        distance = abs(float(cell.center[1]) - fixed_y_m)
        current = selected_by_x.get(x_key)
        if current is None or distance < current[0]:
            selected_by_x[x_key] = (distance, cell.index)

    rows: list[dict[str, float]] = []
    for _, cell_index in sorted(selected_by_x.values(), key=lambda item: cells[item[1]].center[0]):
        velocity = u_values[cell_index]
        rows.append(
            {
                "x_m": float(cells[cell_index].center[0]),
                "p": float(p_values[cell_index]),
                "rho": float(rho_values[cell_index]),
                "T": float(t_values[cell_index]),
                "Ux": float(velocity[0]),
                "Uy": float(velocity[1]),
                "Uz": float(velocity[2]),
            }
        )
    if len(rows) < 2:
        raise ValueError("C08 shock line sampling produced fewer than two samples.")
    return rows


def sample_shock_line_profile(config: dict[str, Any], output_dir: Path) -> list[dict[str, float]]:
    case_dir = output_dir / "case"
    time_dir = _latest_time_dir(case_dir)
    cells = load_cell_geometry(case_dir)
    fields = _read_case_fields(case_dir, time_dir)
    p_values = fields["p"]
    t_values = fields["T"]
    u_values = fields["U"]
    rho_values = fields.get("rho")
    if rho_values is None:
        gamma = float(config["thermophysical_properties"]["gamma"])
        rho_values = _rho_from_pressure_temperature(p_values, t_values, gamma)

    line = _configured_sample_line(config)
    return select_x_axis_profile_rows(cells, p_values, rho_values, t_values, u_values, float(line["fixed_coordinate_m"]))


def write_shock_metrics(config: dict[str, Any], output_dir: Path, profile_rows: list[dict[str, float]] | None = None) -> dict[str, Any]:
    if profile_rows is None:
        profile_rows = sample_shock_line_profile(config, output_dir)
    shock_search_window = config["postprocess"]["shock_search_window_m"]
    shock_x = locate_shock_position_from_profile(profile_rows, config["postprocess"]["shock_quantity"], shock_search_window)
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
        "shock_search_window_m": shock_search_window,
        "upstream": windows["upstream"],
        "downstream": windows["downstream"],
        **jumps,
        "profile_path": str(profile_path),
    }
    post_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    metrics["path"] = str(metrics_path)
    return metrics


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


def _mean_point(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
        sum(point[2] for point in points) / count,
    )


def _face_area_vector(face_points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if len(face_points) < 3:
        return (0.0, 0.0, 0.0)
    origin = face_points[0]
    area = (0.0, 0.0, 0.0)
    for index in range(1, len(face_points) - 1):
        area = _add(area, _cross(_sub(face_points[index], origin), _sub(face_points[index + 1], origin)))
    return _mul(area, 0.5)


def _relative_flux_imbalance(net_flux: float, gross_flux: float) -> float:
    return abs(net_flux) / gross_flux if gross_flux > 0.0 else math.inf


def compute_boundary_flux_conservation_proxy(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / "case"
    time_dir = _latest_time_dir(case_dir)
    cells = load_cell_geometry(case_dir)
    cell_count = len(cells)
    poly_dir = case_dir / "constant" / "polyMesh"
    points = read_points(poly_dir / "points")
    faces = read_faces(poly_dir / "faces")
    owners = read_label_list(poly_dir / "owner")
    boundary = read_boundary(poly_dir / "boundary")
    final_fields = _read_case_fields(case_dir, time_dir)
    gamma = float(config["thermophysical_properties"]["gamma"])
    cv = 1.0 / (gamma * (gamma - 1.0))

    p_final = expand_uniform_scalars(final_fields["p"], cell_count)
    t_final = expand_uniform_scalars(final_fields["T"], cell_count)
    u_final = expand_uniform_vectors(final_fields["U"], cell_count)
    rho_field = final_fields.get("rho")
    rho_final = expand_uniform_scalars(rho_field, cell_count) if rho_field is not None else _rho_from_pressure_temperature(p_final, t_final, gamma)

    rows: list[dict[str, Any]] = []
    for patch_name, patch in boundary.items():
        if patch.get("type") == "empty":
            continue
        start = int(patch["startFace"])
        stop = start + int(patch["nFaces"])
        mass_flux = 0.0
        energy_flux = 0.0
        gross_mass_flux = 0.0
        gross_energy_flux = 0.0
        for face_index in range(start, stop):
            owner = owners[face_index]
            face_points = [points[item] for item in faces[face_index]]
            face_center = _mean_point(face_points)
            area_vector = _face_area_vector(face_points)
            if _dot(area_vector, _sub(face_center, cells[owner].center)) < 0.0:
                area_vector = _mul(area_vector, -1.0)
            face_mass_flux = float(rho_final[owner]) * _dot(u_final[owner], area_vector)
            kinetic = 0.5 * _dot(u_final[owner], u_final[owner])
            specific_total_enthalpy_proxy = cv * float(t_final[owner]) + kinetic + float(p_final[owner]) / max(float(rho_final[owner]), 1e-30)
            face_energy_flux = face_mass_flux * specific_total_enthalpy_proxy
            mass_flux += face_mass_flux
            energy_flux += face_energy_flux
            gross_mass_flux += abs(face_mass_flux)
            gross_energy_flux += abs(face_energy_flux)
        rows.append(
            {
                "patch": patch_name,
                "patch_type": patch.get("type", ""),
                "face_count": int(patch["nFaces"]),
                "mass_flux_proxy": mass_flux,
                "energy_flux_proxy": energy_flux,
                "gross_mass_flux_proxy": gross_mass_flux,
                "gross_energy_flux_proxy": gross_energy_flux,
            }
        )

    net_mass_flux = sum(float(row["mass_flux_proxy"]) for row in rows)
    gross_mass_flux = sum(float(row["gross_mass_flux_proxy"]) for row in rows)
    net_energy_flux = sum(float(row["energy_flux_proxy"]) for row in rows)
    gross_energy_flux = sum(float(row["gross_energy_flux_proxy"]) for row in rows)
    mass_imbalance = _relative_flux_imbalance(net_mass_flux, gross_mass_flux)
    energy_imbalance = _relative_flux_imbalance(net_energy_flux, gross_energy_flux)
    flux_path = output_dir / "postprocess" / "boundary_flux_summary.csv"
    _write_csv(
        flux_path,
        [
            "patch",
            "patch_type",
            "face_count",
            "mass_flux_proxy",
            "energy_flux_proxy",
            "gross_mass_flux_proxy",
            "gross_energy_flux_proxy",
        ],
        rows,
    )

    return {
        "method": "boundary_flux_owner_cell_proxy",
        "time_dir": str(time_dir),
        "included_patches": [str(row["patch"]) for row in rows],
        "net_mass_flux_proxy": net_mass_flux,
        "gross_mass_flux_proxy": gross_mass_flux,
        "boundary_flux_mass_imbalance_proxy": mass_imbalance,
        "net_energy_flux_proxy": net_energy_flux,
        "gross_energy_flux_proxy": gross_energy_flux,
        "boundary_flux_total_energy_imbalance_proxy": energy_imbalance,
        "boundary_flux_path": str(flux_path),
        "limitation": "Boundary fluxes use owner-cell values and oriented polyMesh face areas; this is a reproducible OpenFOAM-field proxy, not native rhoPhi/phi integration.",
    }


def write_conservation_summary(
    output_dir: Path,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner_cell_proxy = {
        "available": bool(details) and details.get("method") == "boundary_flux_owner_cell_proxy",
    }
    if details:
        owner_cell_proxy.update(details)
    summary = {
        "available": owner_cell_proxy["available"],
        "owner_cell_proxy": owner_cell_proxy,
        "flux_parity": {
            "available": False,
            "method": "not_configured",
            "reason": "native OpenFOAM face flux or independently reviewed face-field parity has not been generated for this run",
        },
    }
    path = output_dir / "postprocess" / "conservation_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["path"] = str(path)
    return summary
