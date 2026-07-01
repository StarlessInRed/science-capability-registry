"""Post-processing helpers for OpenFOAM C07 conjugate heat transfer runs."""

from __future__ import annotations

from csv import DictWriter
from dataclasses import dataclass
from math import fsum, isfinite
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import (
    expand_uniform_scalars,
    read_boundary,
    read_boundary_scalars,
    read_faces,
    read_internal_scalars,
    read_label_list,
    read_points,
)


@dataclass(frozen=True)
class PatchSample:
    face_index: int
    owner_cell: int
    face_center: tuple[float, float, float]
    cell_center: tuple[float, float, float]
    area_m2: float


def _case_id(config: dict[str, Any]) -> str:
    return str(config.get("case_id", "openfoam_c07"))


def _regions(config: dict[str, Any]) -> list[str]:
    return [*config["regions"]["fluid"], *config["regions"]["solid"]]


def _time_dir_name(config: dict[str, Any], final_time: float | None) -> str:
    if final_time is not None:
        return f"{final_time:g}"
    return f"{float(config['numerics']['control']['end_time_iterations']):g}"


def _summary(values: list[float]) -> dict[str, Any]:
    finite_values = [value for value in values if isfinite(value)]
    if not finite_values:
        return {
            "sample_count": 0,
            "min_T_K": None,
            "max_T_K": None,
            "mean_T_K": None,
            "finite": False,
        }
    return {
        "sample_count": len(finite_values),
        "min_T_K": min(finite_values),
        "max_T_K": max(finite_values),
        "mean_T_K": fsum(finite_values) / len(finite_values),
        "finite": len(finite_values) == len(values),
    }


def _mean(values: list[float]) -> float | None:
    finite_values = [value for value in values if isfinite(value)]
    return fsum(finite_values) / len(finite_values) if finite_values else None


def _mean_point(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
        sum(point[2] for point in points) / count,
    )


def _distance(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> float:
    return (
        (first[0] - second[0]) ** 2
        + (first[1] - second[1]) ** 2
        + (first[2] - second[2]) ** 2
    ) ** 0.5


def _region_poly_dir(output_dir: Path, region: str) -> Path:
    return output_dir / "case" / "constant" / region / "polyMesh"


def _load_region_cell_vertices(output_dir: Path, region: str) -> tuple[list[tuple[float, float, float]], list[list[int]], list[int], list[set[int]]]:
    poly = _region_poly_dir(output_dir, region)
    points = read_points(poly / "points")
    faces = read_faces(poly / "faces")
    owner = read_label_list(poly / "owner")
    neighbour = read_label_list(poly / "neighbour")
    cell_count = max(owner + neighbour) + 1 if neighbour else max(owner) + 1
    cell_vertices = [set() for _ in range(cell_count)]
    for face_index, face in enumerate(faces):
        owner_cell = owner[face_index]
        cell_vertices[owner_cell].update(face)
        if face_index < len(neighbour):
            cell_vertices[neighbour[face_index]].update(face)
    return points, faces, owner, cell_vertices


def _load_region_cell_count(output_dir: Path, region: str) -> int:
    return len(_load_region_cell_vertices(output_dir, region)[3])


def _face_area(points: list[tuple[float, float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    origin = points[0]
    area = 0.0
    for index in range(1, len(points) - 1):
        first = (
            points[index][0] - origin[0],
            points[index][1] - origin[1],
            points[index][2] - origin[2],
        )
        second = (
            points[index + 1][0] - origin[0],
            points[index + 1][1] - origin[1],
            points[index + 1][2] - origin[2],
        )
        cross = (
            first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0],
        )
        area += 0.5 * _distance(cross, (0.0, 0.0, 0.0))
    return area


def _load_region_patch_samples(output_dir: Path, region: str, patch_name: str) -> list[PatchSample]:
    poly = _region_poly_dir(output_dir, region)
    points, faces, owner, cell_vertices = _load_region_cell_vertices(output_dir, region)
    cell_centers = [_mean_point([points[item] for item in sorted(vertices)]) for vertices in cell_vertices]
    boundary = read_boundary(poly / "boundary")
    if patch_name not in boundary:
        raise ValueError(f"Patch {patch_name!r} not found in {poly / 'boundary'}")
    patch = boundary[patch_name]
    start = int(patch["startFace"])
    stop = start + int(patch["nFaces"])
    samples = []
    for face_index in range(start, stop):
        face_points = [points[item] for item in faces[face_index]]
        owner_cell = owner[face_index]
        samples.append(
            PatchSample(
                face_index=face_index,
                owner_cell=owner_cell,
                face_center=_mean_point(face_points),
                cell_center=cell_centers[owner_cell],
                area_m2=_face_area(face_points),
            )
        )
    return samples


def _patch_cell_temperatures(config: dict[str, Any], output_dir: Path, region: str, time_name: str) -> list[float]:
    cell_count = _load_region_cell_count(output_dir, region)
    values = read_internal_scalars(output_dir / "case" / time_name / region / "T")
    return expand_uniform_scalars(values, cell_count)


def _region_conductivity(config: dict[str, Any], region: str) -> float:
    material = config["materials"][region]
    if "thermal_conductivity_W_m_K" in material:
        return float(material["thermal_conductivity_W_m_K"])
    return (
        float(material["dynamic_viscosity_Pa_s"])
        * float(material["cp_J_kg_K"])
        / float(material["prandtl"])
    )


def _patch_temperature_mean(faces: list[PatchSample], temperatures: list[float]) -> float | None:
    values = [temperatures[face.owner_cell] for face in faces if 0 <= face.owner_cell < len(temperatures)]
    return _mean(values)


def _patch_value_mean(values: list[float]) -> float | None:
    return _mean(values)


def _nearest_sample_pairs(owner_faces: list[PatchSample], neighbour_faces: list[PatchSample]) -> list[tuple[PatchSample, PatchSample, float]]:
    remaining = list(neighbour_faces)
    pairs = []
    for owner_face in owner_faces:
        if not remaining:
            break
        nearest_index = min(
            range(len(remaining)),
            key=lambda index: _distance(owner_face.face_center, remaining[index].face_center),
        )
        neighbour_face = remaining.pop(nearest_index)
        pairs.append((owner_face, neighbour_face, _distance(owner_face.face_center, neighbour_face.face_center)))
    return pairs


def _patch_boundary_temperatures(output_dir: Path, region: str, time_name: str, patch_name: str, face_count: int) -> list[float]:
    field_path = output_dir / "case" / time_name / region / "T"
    return read_boundary_scalars(field_path, patch_name, "value", expected_count=face_count)


def _face_heat_rate_outward(face: PatchSample, cell_temperature: float, patch_temperature: float, conductivity: float) -> float:
    distance = max(_distance(face.cell_center, face.face_center), 1.0e-12)
    normal_gradient = (patch_temperature - cell_temperature) / distance
    return -conductivity * normal_gradient * face.area_m2


def _relative_pair_mismatch(owner_heat_rate: float, neighbour_heat_rate: float) -> float:
    denominator = max(abs(owner_heat_rate), abs(neighbour_heat_rate), 1.0e-30)
    return abs(owner_heat_rate + neighbour_heat_rate) / denominator


def write_region_temperature_summary(
    config: dict[str, Any],
    output_dir: Path,
    final_time: float | None = None,
) -> dict[str, Any]:
    """Write per-region T-field min/max/mean summaries."""

    time_name = _time_dir_name(config, final_time)
    rows = []
    for region in _regions(config):
        field_path = output_dir / "case" / time_name / region / "T"
        values = read_internal_scalars(field_path) if field_path.exists() else []
        rows.append(
            {
                "case_id": _case_id(config),
                "time": time_name,
                "region": region,
                "field_path": str(field_path),
                "available": bool(values),
                **_summary(values),
            }
        )

    post_dir = output_dir / "postprocess"
    post_dir.mkdir(parents=True, exist_ok=True)
    csv_path = post_dir / "region_temperature_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "time",
                "region",
                "field_path",
                "available",
                "sample_count",
                "min_T_K",
                "max_T_K",
                "mean_T_K",
                "finite",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {"csv": str(csv_path), "time": time_name, "available": any(row["available"] for row in rows), "regions": rows}


def write_interface_balance_summary(
    config: dict[str, Any],
    output_dir: Path,
    temperature_summary: dict[str, Any],
) -> dict[str, Any]:
    """Write a coarse interface continuity proxy without claiming heat-flux validation."""

    rows_by_region = {
        str(row["region"]): row for row in temperature_summary.get("regions", []) if row.get("available")
    }
    rows = []
    for interface in config.get("interfaces", []):
        owner_region = interface["owner_region"]
        neighbour_region = interface["neighbour_region"]
        owner = rows_by_region.get(owner_region)
        neighbour = rows_by_region.get(neighbour_region)
        owner_mean = owner.get("mean_T_K") if owner else None
        neighbour_mean = neighbour.get("mean_T_K") if neighbour else None
        delta = abs(float(owner_mean) - float(neighbour_mean)) if owner_mean is not None and neighbour_mean is not None else None
        rows.append(
            {
                "case_id": _case_id(config),
                "time": temperature_summary.get("time", ""),
                "interface": interface["name"],
                "owner_region": owner_region,
                "neighbour_region": neighbour_region,
                "owner_mean_T_K": owner_mean,
                "neighbour_mean_T_K": neighbour_mean,
                "mean_abs_delta_T_K": delta,
                "proxy_method": "region_mean_temperature_difference",
                "heat_flux_relative_mismatch_available": False,
            }
        )

    post_dir = output_dir / "postprocess"
    post_dir.mkdir(parents=True, exist_ok=True)
    csv_path = post_dir / "interface_balance_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "time",
                "interface",
                "owner_region",
                "neighbour_region",
                "owner_mean_T_K",
                "neighbour_mean_T_K",
                "mean_abs_delta_T_K",
                "proxy_method",
                "heat_flux_relative_mismatch_available",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {
        "csv": str(csv_path),
        "available": any(row["mean_abs_delta_T_K"] is not None for row in rows),
        "interfaces": rows,
    }


def write_patch_heat_flux_proxy_summary(
    config: dict[str, Any],
    output_dir: Path,
    temperature_summary: dict[str, Any],
) -> dict[str, Any]:
    """Write a patch-face heat-flux proxy for CHT interface trend checks."""

    time_name = str(temperature_summary.get("time") or _time_dir_name(config, None))
    rows = []
    for interface in config.get("interfaces", []):
        base_row: dict[str, Any] = {
            "case_id": _case_id(config),
            "time": time_name,
            "interface": interface["name"],
            "owner_region": interface["owner_region"],
            "neighbour_region": interface["neighbour_region"],
            "owner_patch": interface["owner_patch"],
            "neighbour_patch": interface["neighbour_patch"],
            "proxy_method": "paired_patch_owner_cell_series_resistance_proxy",
        }
        try:
            owner_faces = _load_region_patch_samples(output_dir, interface["owner_region"], interface["owner_patch"])
            neighbour_faces = _load_region_patch_samples(
                output_dir, interface["neighbour_region"], interface["neighbour_patch"]
            )
            owner_temperatures = _patch_cell_temperatures(config, output_dir, interface["owner_region"], time_name)
            neighbour_temperatures = _patch_cell_temperatures(
                config, output_dir, interface["neighbour_region"], time_name
            )
            owner_mean = _patch_temperature_mean(owner_faces, owner_temperatures)
            neighbour_mean = _patch_temperature_mean(neighbour_faces, neighbour_temperatures)
            if owner_mean is None or neighbour_mean is None:
                raise ValueError("Patch faces or owner-cell temperatures are empty.")
            owner_k = _region_conductivity(config, interface["owner_region"])
            neighbour_k = _region_conductivity(config, interface["neighbour_region"])
            pairs = _nearest_sample_pairs(owner_faces, neighbour_faces)
            if not pairs:
                raise ValueError("No patch-face pairs are available.")
            heat_rates = []
            heat_fluxes = []
            pairing_distances = []
            paired_areas = []
            for owner_face, neighbour_face, pairing_distance in pairs:
                owner_t = owner_temperatures[owner_face.owner_cell]
                neighbour_t = neighbour_temperatures[neighbour_face.owner_cell]
                owner_distance = max(_distance(owner_face.cell_center, owner_face.face_center), 1.0e-12)
                neighbour_distance = max(_distance(neighbour_face.cell_center, neighbour_face.face_center), 1.0e-12)
                thermal_resistance = owner_distance / owner_k + neighbour_distance / neighbour_k
                heat_flux = (owner_t - neighbour_t) / max(thermal_resistance, 1.0e-18)
                paired_area = min(owner_face.area_m2, neighbour_face.area_m2)
                heat_fluxes.append(heat_flux)
                heat_rates.append(heat_flux * paired_area)
                paired_areas.append(paired_area)
                pairing_distances.append(pairing_distance)
            paired_area_sum = fsum(paired_areas)
            heat_rate_sum = fsum(heat_rates)
            mean_heat_flux = heat_rate_sum / paired_area_sum if paired_area_sum > 0.0 else None
            rows.append(
                {
                    **base_row,
                    "available": True,
                    "owner_patch_face_count": len(owner_faces),
                    "neighbour_patch_face_count": len(neighbour_faces),
                    "paired_face_count": len(pairs),
                    "owner_area_m2": fsum(face.area_m2 for face in owner_faces),
                    "neighbour_area_m2": fsum(face.area_m2 for face in neighbour_faces),
                    "paired_area_m2": paired_area_sum,
                    "owner_patch_mean_T_K": owner_mean,
                    "neighbour_patch_mean_T_K": neighbour_mean,
                    "owner_conductivity_W_m_K": owner_k,
                    "neighbour_conductivity_W_m_K": neighbour_k,
                    "mean_pairing_distance_m": _mean(pairing_distances),
                    "max_pairing_distance_m": max(pairing_distances),
                    "owner_to_neighbour_flux_proxy_W_m2": mean_heat_flux,
                    "owner_to_neighbour_heat_rate_proxy_W": heat_rate_sum,
                    "relative_mismatch_proxy": 0.0,
                    "failure_reason": "",
                }
            )
        except (OSError, ValueError, IndexError) as exc:
            rows.append(
                {
                    **base_row,
                    "available": False,
                    "owner_patch_face_count": 0,
                    "neighbour_patch_face_count": 0,
                    "paired_face_count": 0,
                    "owner_area_m2": None,
                    "neighbour_area_m2": None,
                    "paired_area_m2": None,
                    "owner_patch_mean_T_K": None,
                    "neighbour_patch_mean_T_K": None,
                    "owner_conductivity_W_m_K": None,
                    "neighbour_conductivity_W_m_K": None,
                    "mean_pairing_distance_m": None,
                    "max_pairing_distance_m": None,
                    "owner_to_neighbour_flux_proxy_W_m2": None,
                    "owner_to_neighbour_heat_rate_proxy_W": None,
                    "relative_mismatch_proxy": None,
                    "failure_reason": str(exc),
                }
            )

    post_dir = output_dir / "postprocess"
    post_dir.mkdir(parents=True, exist_ok=True)
    csv_path = post_dir / "patch_heat_flux_proxy_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "time",
                "interface",
                "owner_region",
                "neighbour_region",
                "owner_patch",
                "neighbour_patch",
                "available",
                "owner_patch_face_count",
                "neighbour_patch_face_count",
                "paired_face_count",
                "owner_area_m2",
                "neighbour_area_m2",
                "paired_area_m2",
                "owner_patch_mean_T_K",
                "neighbour_patch_mean_T_K",
                "owner_conductivity_W_m_K",
                "neighbour_conductivity_W_m_K",
                "mean_pairing_distance_m",
                "max_pairing_distance_m",
                "owner_to_neighbour_flux_proxy_W_m2",
                "owner_to_neighbour_heat_rate_proxy_W",
                "relative_mismatch_proxy",
                "proxy_method",
                "failure_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {
        "csv": str(csv_path),
        "available": bool(rows) and all(row["available"] for row in rows),
        "interfaces": rows,
    }


def write_interface_heat_flux_field_summary(
    config: dict[str, Any],
    output_dir: Path,
    temperature_summary: dict[str, Any],
) -> dict[str, Any]:
    """Write an independent two-sided patch-gradient heat-rate balance."""

    time_name = str(temperature_summary.get("time") or _time_dir_name(config, None))
    rows = []
    for interface in config.get("interfaces", []):
        base_row: dict[str, Any] = {
            "case_id": _case_id(config),
            "time": time_name,
            "interface": interface["name"],
            "owner_region": interface["owner_region"],
            "neighbour_region": interface["neighbour_region"],
            "owner_patch": interface["owner_patch"],
            "neighbour_patch": interface["neighbour_patch"],
            "method": "face_field_integration",
        }
        try:
            owner_faces = _load_region_patch_samples(output_dir, interface["owner_region"], interface["owner_patch"])
            neighbour_faces = _load_region_patch_samples(
                output_dir, interface["neighbour_region"], interface["neighbour_patch"]
            )
            owner_temperatures = _patch_cell_temperatures(config, output_dir, interface["owner_region"], time_name)
            neighbour_temperatures = _patch_cell_temperatures(
                config, output_dir, interface["neighbour_region"], time_name
            )
            owner_patch_temperatures = _patch_boundary_temperatures(
                output_dir,
                interface["owner_region"],
                time_name,
                interface["owner_patch"],
                len(owner_faces),
            )
            neighbour_patch_temperatures = _patch_boundary_temperatures(
                output_dir,
                interface["neighbour_region"],
                time_name,
                interface["neighbour_patch"],
                len(neighbour_faces),
            )
            owner_face_indices = {face.face_index: index for index, face in enumerate(owner_faces)}
            neighbour_face_indices = {face.face_index: index for index, face in enumerate(neighbour_faces)}
            pairs = _nearest_sample_pairs(owner_faces, neighbour_faces)
            if not pairs:
                raise ValueError("No patch-face pairs are available.")
            owner_k = _region_conductivity(config, interface["owner_region"])
            neighbour_k = _region_conductivity(config, interface["neighbour_region"])
            owner_heat_rates = []
            neighbour_heat_rates = []
            pair_mismatches = []
            pairing_distances = []
            for owner_face, neighbour_face, pairing_distance in pairs:
                owner_patch_index = owner_face_indices[owner_face.face_index]
                neighbour_patch_index = neighbour_face_indices[neighbour_face.face_index]
                owner_heat_rate = _face_heat_rate_outward(
                    owner_face,
                    owner_temperatures[owner_face.owner_cell],
                    owner_patch_temperatures[owner_patch_index],
                    owner_k,
                )
                neighbour_heat_rate = _face_heat_rate_outward(
                    neighbour_face,
                    neighbour_temperatures[neighbour_face.owner_cell],
                    neighbour_patch_temperatures[neighbour_patch_index],
                    neighbour_k,
                )
                owner_heat_rates.append(owner_heat_rate)
                neighbour_heat_rates.append(neighbour_heat_rate)
                pair_mismatches.append(_relative_pair_mismatch(owner_heat_rate, neighbour_heat_rate))
                pairing_distances.append(pairing_distance)
            owner_heat_rate_sum = fsum(owner_heat_rates)
            neighbour_heat_rate_sum = fsum(neighbour_heat_rates)
            net_heat_rate = owner_heat_rate_sum + neighbour_heat_rate_sum
            denominator = max(abs(owner_heat_rate_sum), abs(neighbour_heat_rate_sum), 1.0e-30)
            rows.append(
                {
                    **base_row,
                    "available": True,
                    "owner_patch_face_count": len(owner_faces),
                    "neighbour_patch_face_count": len(neighbour_faces),
                    "paired_face_count": len(pairs),
                    "owner_area_m2": fsum(face.area_m2 for face in owner_faces),
                    "neighbour_area_m2": fsum(face.area_m2 for face in neighbour_faces),
                    "owner_patch_value_mean_T_K": _patch_value_mean(owner_patch_temperatures),
                    "neighbour_patch_value_mean_T_K": _patch_value_mean(neighbour_patch_temperatures),
                    "owner_conductivity_W_m_K": owner_k,
                    "neighbour_conductivity_W_m_K": neighbour_k,
                    "owner_outward_heat_rate_W": owner_heat_rate_sum,
                    "neighbour_outward_heat_rate_W": neighbour_heat_rate_sum,
                    "net_interface_heat_rate_W": net_heat_rate,
                    "relative_heat_rate_mismatch": abs(net_heat_rate) / denominator,
                    "max_pair_relative_mismatch": max(pair_mismatches),
                    "mean_pairing_distance_m": _mean(pairing_distances),
                    "max_pairing_distance_m": max(pairing_distances),
                    "failure_reason": "",
                }
            )
        except (OSError, ValueError, IndexError) as exc:
            rows.append(
                {
                    **base_row,
                    "available": False,
                    "owner_patch_face_count": 0,
                    "neighbour_patch_face_count": 0,
                    "paired_face_count": 0,
                    "owner_area_m2": None,
                    "neighbour_area_m2": None,
                    "owner_patch_value_mean_T_K": None,
                    "neighbour_patch_value_mean_T_K": None,
                    "owner_conductivity_W_m_K": None,
                    "neighbour_conductivity_W_m_K": None,
                    "owner_outward_heat_rate_W": None,
                    "neighbour_outward_heat_rate_W": None,
                    "net_interface_heat_rate_W": None,
                    "relative_heat_rate_mismatch": None,
                    "max_pair_relative_mismatch": None,
                    "mean_pairing_distance_m": None,
                    "max_pairing_distance_m": None,
                    "failure_reason": str(exc),
                }
            )

    post_dir = output_dir / "postprocess"
    post_dir.mkdir(parents=True, exist_ok=True)
    csv_path = post_dir / "interface_heat_flux_field_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "time",
                "interface",
                "owner_region",
                "neighbour_region",
                "owner_patch",
                "neighbour_patch",
                "method",
                "available",
                "owner_patch_face_count",
                "neighbour_patch_face_count",
                "paired_face_count",
                "owner_area_m2",
                "neighbour_area_m2",
                "owner_patch_value_mean_T_K",
                "neighbour_patch_value_mean_T_K",
                "owner_conductivity_W_m_K",
                "neighbour_conductivity_W_m_K",
                "owner_outward_heat_rate_W",
                "neighbour_outward_heat_rate_W",
                "net_interface_heat_rate_W",
                "relative_heat_rate_mismatch",
                "max_pair_relative_mismatch",
                "mean_pairing_distance_m",
                "max_pairing_distance_m",
                "failure_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {
        "csv": str(csv_path),
        "available": bool(rows) and all(row["available"] for row in rows),
        "interfaces": rows,
        "max_relative_heat_rate_mismatch": max(
            (
                float(row["relative_heat_rate_mismatch"])
                for row in rows
                if row["available"] and row["relative_heat_rate_mismatch"] is not None
            ),
            default=None,
        ),
    }
