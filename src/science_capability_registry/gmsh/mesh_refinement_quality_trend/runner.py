"""Runner for Gmsh C03 refinement and quality trend contracts."""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_refinement_metrics, validate_manifest
from ..mesh_summary import import_gmsh, summarize_current_mesh

SCHEMA_ID = "schemas/gmsh_C03_mesh_refinement_quality_trend.schema.json"


def _write_refinement_matrix(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = output_dir / "refinement_matrix.csv"
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "level_id",
                "characteristic_length_m",
                "algorithm",
                "element_order",
                "expected_node_count_min",
                "expected_element_count_min",
                "expected_min_quality_proxy",
                "expected_max_aspect_ratio_proxy",
                "nonfinite_coordinate_count",
            ],
        )
        writer.writeheader()
        writer.writerows(config["refinement_levels"])
    summary = {
        "geometry_contract": config["geometry_contract"],
        "quality_thresholds": config["quality_thresholds"],
        "refinement_levels": config["refinement_levels"],
        "trend_expectations": config["trend_expectations"],
    }
    (output_dir / "mesh_quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return ["refinement_matrix.csv", "mesh_quality_summary.json"]


def _build_rectangle_mesh(gmsh: Any, config: dict[str, Any], level: dict[str, Any], level_dir: Path) -> dict[str, Any]:
    geometry = config["geometry_parameters"]
    x0, y0 = geometry["origin_m"]
    length = float(geometry["length_m"])
    height = float(geometry["height_m"])
    lc = float(level["characteristic_length_m"])
    x1 = float(x0) + length
    y1 = float(y0) + height
    gmsh.model.add(f"c03_{level['level_id']}")
    p1 = gmsh.model.geo.addPoint(float(x0), float(y0), 0.0, lc)
    p2 = gmsh.model.geo.addPoint(x1, float(y0), 0.0, lc)
    p3 = gmsh.model.geo.addPoint(x1, y1, 0.0, lc)
    p4 = gmsh.model.geo.addPoint(float(x0), y1, 0.0, lc)
    l1 = gmsh.model.geo.addLine(p1, p2)
    l2 = gmsh.model.geo.addLine(p2, p3)
    l3 = gmsh.model.geo.addLine(p3, p4)
    l4 = gmsh.model.geo.addLine(p4, p1)
    loop = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4])
    surface = gmsh.model.geo.addPlaneSurface([loop])
    gmsh.model.geo.synchronize()
    inlet = gmsh.model.addPhysicalGroup(1, [l4])
    outlet = gmsh.model.addPhysicalGroup(1, [l2])
    wall = gmsh.model.addPhysicalGroup(1, [l1, l3])
    domain = gmsh.model.addPhysicalGroup(2, [surface])
    gmsh.model.setPhysicalName(1, inlet, "inlet")
    gmsh.model.setPhysicalName(1, outlet, "outlet")
    gmsh.model.setPhysicalName(1, wall, "wall")
    gmsh.model.setPhysicalName(2, domain, "fluid_domain")
    gmsh.option.setNumber("Mesh.ElementOrder", int(level["element_order"]))
    gmsh.option.setNumber("Mesh.Algorithm", int(level["algorithm"]))
    gmsh.model.mesh.generate(2)
    level_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = level_dir / "case.msh"
    gmsh.write(str(mesh_path))
    summary = summarize_current_mesh(gmsh, 2)
    summary["level_id"] = level["level_id"]
    summary["characteristic_length_m"] = level["characteristic_length_m"]
    summary["algorithm"] = level["algorithm"]
    summary["element_order"] = level["element_order"]
    summary["artifacts"] = {"case.msh": str(mesh_path)}
    return summary


def _run_python_api(output_dir: Path, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    gmsh = import_gmsh()
    summaries = []
    generated_files = _write_refinement_matrix(output_dir, config)
    gmsh.initialize()
    try:
        for level in config["refinement_levels"]:
            gmsh.clear()
            level_dir = output_dir / "levels" / level["level_id"]
            summary = _build_rectangle_mesh(gmsh, config, level, level_dir)
            summaries.append(summary)
            generated_files.append(f"levels/{level['level_id']}/case.msh")
    finally:
        gmsh.finalize()

    runtime_config = deepcopy(config)
    for level, summary in zip(runtime_config["refinement_levels"], summaries):
        level["expected_node_count_min"] = int(summary["node_count"])
        level["expected_element_count_min"] = int(summary["element_count"])
        level["expected_min_quality_proxy"] = float(summary["quality"]["min_quality_proxy"])
        aspect_ratio = summary["quality"].get("max_aspect_ratio_proxy")
        level["expected_max_aspect_ratio_proxy"] = float(aspect_ratio) if aspect_ratio is not None else 1.0
        level["nonfinite_coordinate_count"] = 0 if summary["coordinates_finite"] else 1
    runtime_summary = {
        "backend": "python_api",
        "geometry_parameters": config["geometry_parameters"],
        "level_summaries": summaries,
    }
    (output_dir / "mesh_quality_summary.json").write_text(json.dumps(runtime_summary, indent=2), encoding="utf-8")
    return runtime_config, generated_files


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "geometry_contract": config["geometry_contract"],
        "quality_thresholds": config["quality_thresholds"],
        "refinement_levels": config["refinement_levels"],
        "trend_expectations": config["trend_expectations"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build refinement_matrix.csv",
            "static-contract:build mesh_quality_summary.json",
        ],
        "scope": "static refinement trend contract; no mesh generation or solver execution",
    }


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
    backend: str | None = None,
) -> dict[str, Any]:
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)
    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_case_config(config)

    backend_type = config["backend"]["type"]
    if not dry_run and backend_type != "python_api":
        raise ValueError("Gmsh C03 non-dry-run requires backend.type=python_api.")
    if dry_run and backend_type not in {"dry_run_only", "python_api"}:
        raise NotImplementedError(f"Gmsh C03 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    runtime_summary: dict[str, Any] | None = None
    if dry_run or backend_type == "dry_run_only":
        generated_files = _write_refinement_matrix(resolved_output_dir, config)
        validation_config = config
    else:
        validation_config, generated_files = _run_python_api(resolved_output_dir, config)
        runtime_summary = {
            "backend": "python_api",
            "level_count": len(validation_config["refinement_levels"]),
        }
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(validation_config, resolved_output_dir, generated_files)
    if runtime_summary is not None:
        manifest["runtime"] = runtime_summary
    validation = validate_manifest(manifest, validation_config)
    metrics = summarize_refinement_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, validation_config, resolved_output_dir)
    metrics = summarize_refinement_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
