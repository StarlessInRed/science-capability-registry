"""Post-processing helpers for C08 shock metrics."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import (
    CellGeometry,
    expand_uniform_scalars,
    expand_uniform_vectors,
    load_cell_geometry,
    read_internal_scalars,
    read_internal_vectors,
)

PROFILE_COLUMNS = ["x_m", "p", "rho", "T", "Ux", "Uy", "Uz"]
FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
VECTOR_RE = re.compile(rf"\(\s*({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*\)")


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


def _parse_vector(text: str) -> tuple[float, float, float]:
    match = VECTOR_RE.fullmatch(str(text).strip())
    if match is None:
        raise ValueError(f"Expected OpenFOAM vector text, got {text!r}")
    return (float(match.group(1)), float(match.group(2)), float(match.group(3)))


def compute_inventory_conservation_proxy(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    case_dir = output_dir / "case"
    time_dir = _latest_time_dir(case_dir)
    cells = load_cell_geometry(case_dir)
    volumes = [cell.volume for cell in cells]
    final_fields = _read_case_fields(case_dir, time_dir)
    gamma = float(config["thermophysical_properties"]["gamma"])
    cv = 1.0 / (gamma * (gamma - 1.0))

    p_initial = float(config["fields"]["p"]["initial_value"])
    t_initial = float(config["fields"]["T"]["initial_value"])
    u_initial = _parse_vector(config["fields"]["U"]["initial_value"])
    rho_initial = gamma * p_initial / t_initial
    initial_specific_energy = cv * t_initial + 0.5 * sum(component * component for component in u_initial)

    rho_final = final_fields.get("rho")
    if rho_final is None:
        rho_final = _rho_from_pressure_temperature(final_fields["p"], final_fields["T"], gamma)
    t_final = final_fields["T"]
    u_final = final_fields["U"]

    initial_mass = sum(rho_initial * volume for volume in volumes)
    final_mass = sum(float(rho) * volume for rho, volume in zip(rho_final, volumes))
    initial_energy = sum(rho_initial * initial_specific_energy * volume for volume in volumes)
    final_energy = 0.0
    for rho, temperature, velocity, volume in zip(rho_final, t_final, u_final, volumes):
        kinetic = 0.5 * sum(component * component for component in velocity)
        final_energy += float(rho) * (cv * float(temperature) + kinetic) * volume

    return {
        "method": "open_domain_inventory_relative_change",
        "time_dir": str(time_dir),
        "initial_mass": initial_mass,
        "final_mass": final_mass,
        "initial_energy_proxy": initial_energy,
        "final_energy_proxy": final_energy,
        "mass_conservation_error": abs(final_mass - initial_mass) / abs(initial_mass) if initial_mass else math.inf,
        "energy_conservation_proxy": abs(final_energy - initial_energy) / abs(initial_energy) if initial_energy else math.inf,
        "limitation": "Forward-step runtime has open inlet/outlet boundaries; this proxy measures domain inventory change, not a closed-control-volume flux balance.",
    }


def write_conservation_summary(
    output_dir: Path,
    mass_error: float | None = None,
    energy_error: float | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "available": mass_error is not None and energy_error is not None,
        "mass_conservation_error": mass_error,
        "energy_conservation_proxy": energy_error,
    }
    if details:
        summary.update(details)
    path = output_dir / "postprocess" / "conservation_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["path"] = str(path)
    return summary
