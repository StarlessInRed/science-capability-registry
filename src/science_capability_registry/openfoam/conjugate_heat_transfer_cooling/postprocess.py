"""Post-processing helpers for OpenFOAM C07 conjugate heat transfer runs."""

from __future__ import annotations

from csv import DictWriter
from math import fsum, isfinite
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import read_internal_scalars


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
