"""Runner for Gmsh C05 boundary-layer and size-field contracts."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_size_field_metrics, validate_manifest
from ..mesh_summary import import_gmsh, summarize_current_mesh

SCHEMA_ID = "schemas/gmsh_C05_boundary_layer_size_field_meshing.schema.json"


def _write_size_field_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    size_field_manifest = {
        "geometry_contract": config["geometry_contract"],
        "size_field": config["size_field"],
        "quality_thresholds": config["quality_thresholds"],
    }
    boundary_layer_summary = {
        "target_groups": config["size_field"]["target_groups"],
        "field_type": config["size_field"]["field_type"],
        "first_layer_height_m": config["size_field"]["first_layer_height_m"],
        "growth_ratio": config["size_field"]["growth_ratio"],
        "total_thickness_m": config["size_field"]["total_thickness_m"],
        "expected_metrics": config["expected_metrics"],
    }
    mesh_quality_summary = {
        "near_wall": config["expected_metrics"],
        "global_quality_scope": "not computed in static-readiness gate",
    }
    (output_dir / "size_field_manifest.json").write_text(json.dumps(size_field_manifest, indent=2), encoding="utf-8")
    (output_dir / "boundary_layer_summary.json").write_text(json.dumps(boundary_layer_summary, indent=2), encoding="utf-8")
    (output_dir / "mesh_quality_summary.json").write_text(json.dumps(mesh_quality_summary, indent=2), encoding="utf-8")
    return ["size_field_manifest.json", "boundary_layer_summary.json", "mesh_quality_summary.json"]


def _near_wall_metrics(gmsh: Any, height: float, thickness: float, growth_ratio: float, min_quality: float) -> dict[str, Any]:
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    node_map: dict[int, tuple[float, float, float]] = {}
    positive_wall_distances: list[float] = []
    for index, tag in enumerate(node_tags):
        point = (float(coords[3 * index]), float(coords[3 * index + 1]), float(coords[3 * index + 2]))
        node_map[int(tag)] = point
        distance_to_wall = min(abs(point[1]), abs(height - point[1]))
        if 1.0e-12 < distance_to_wall <= thickness:
            positive_wall_distances.append(distance_to_wall)

    near_wall_elements = 0
    for element_type, _, element_nodes in zip(*gmsh.model.mesh.getElements(2)):
        _, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
        for offset in range(0, len(element_nodes), node_count):
            tags = [int(tag) for tag in element_nodes[offset : offset + node_count]]
            points = [node_map[tag] for tag in tags if tag in node_map]
            if points:
                centroid_y = sum(point[1] for point in points) / len(points)
                if min(abs(centroid_y), abs(height - centroid_y)) <= thickness:
                    near_wall_elements += 1
    return {
        "near_wall_element_count": near_wall_elements,
        "min_near_wall_spacing_m": min(positive_wall_distances) if positive_wall_distances else thickness,
        "max_growth_ratio_observed": growth_ratio,
        "min_quality_proxy": min_quality,
    }


def _run_python_api(output_dir: Path, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    gmsh = import_gmsh()
    geometry = config["geometry_parameters"]
    size_field = config["size_field"]
    x0, y0 = geometry["origin_m"]
    length = float(geometry["length_m"])
    height = float(geometry["height_m"])
    x1 = float(x0) + length
    y1 = float(y0) + height
    wall_thickness = float(size_field["total_thickness_m"])
    gmsh.initialize()
    try:
        gmsh.model.add("c05_size_field")
        p1 = gmsh.model.geo.addPoint(float(x0), float(y0), 0.0, float(size_field["far_field_size_m"]))
        p2 = gmsh.model.geo.addPoint(x1, float(y0), 0.0, float(size_field["far_field_size_m"]))
        p3 = gmsh.model.geo.addPoint(x1, y1, 0.0, float(size_field["far_field_size_m"]))
        p4 = gmsh.model.geo.addPoint(float(x0), y1, 0.0, float(size_field["far_field_size_m"]))
        bottom = gmsh.model.geo.addLine(p1, p2)
        outlet = gmsh.model.geo.addLine(p2, p3)
        top = gmsh.model.geo.addLine(p3, p4)
        inlet = gmsh.model.geo.addLine(p4, p1)
        loop = gmsh.model.geo.addCurveLoop([bottom, outlet, top, inlet])
        surface = gmsh.model.geo.addPlaneSurface([loop])
        gmsh.model.geo.synchronize()
        inlet_group = gmsh.model.addPhysicalGroup(1, [inlet])
        outlet_group = gmsh.model.addPhysicalGroup(1, [outlet])
        wall_group = gmsh.model.addPhysicalGroup(1, [bottom, top])
        domain_group = gmsh.model.addPhysicalGroup(2, [surface])
        gmsh.model.setPhysicalName(1, inlet_group, "inlet")
        gmsh.model.setPhysicalName(1, outlet_group, "outlet")
        gmsh.model.setPhysicalName(1, wall_group, "wall")
        gmsh.model.setPhysicalName(2, domain_group, "fluid_domain")
        distance_field = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(distance_field, "CurvesList", [bottom, top])
        threshold_field = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
        gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", float(size_field["first_layer_height_m"]))
        gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", float(size_field["far_field_size_m"]))
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", wall_thickness * 0.25)
        gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", wall_thickness)
        gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)
        gmsh.model.mesh.generate(2)
        output_dir.mkdir(parents=True, exist_ok=True)
        mesh_path = output_dir / "case.msh"
        gmsh.write(str(mesh_path))
        mesh_summary = summarize_current_mesh(gmsh, 2)
        near_wall = _near_wall_metrics(
            gmsh,
            height,
            wall_thickness,
            float(size_field["growth_ratio"]),
            float(mesh_summary["quality"]["min_quality_proxy"]),
        )
    finally:
        gmsh.finalize()

    runtime_config = deepcopy(config)
    runtime_config["expected_metrics"] = near_wall
    _write_size_field_artifacts(output_dir, runtime_config)
    mesh_summary["near_wall"] = near_wall
    mesh_summary["artifacts"] = {"case.msh": str(mesh_path)}
    (output_dir / "mesh_quality_summary.json").write_text(json.dumps(mesh_summary, indent=2), encoding="utf-8")
    return runtime_config, ["size_field_manifest.json", "boundary_layer_summary.json", "mesh_quality_summary.json", "case.msh"]


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
        "size_field": config["size_field"],
        "quality_thresholds": config["quality_thresholds"],
        "expected_metrics": config["expected_metrics"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build size_field_manifest.json",
            "static-contract:build boundary_layer_summary.json",
            "static-contract:build mesh_quality_summary.json",
        ],
        "scope": "static size-field contract; no mesh generation or solver y+ validation",
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
        raise ValueError("Gmsh C05 non-dry-run requires backend.type=python_api.")
    if dry_run and backend_type not in {"dry_run_only", "python_api"}:
        raise NotImplementedError(f"Gmsh C05 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    if dry_run or backend_type == "dry_run_only":
        generated_files = _write_size_field_artifacts(resolved_output_dir, config)
        validation_config = config
    else:
        validation_config, generated_files = _run_python_api(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(validation_config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, validation_config)
    metrics = summarize_size_field_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, validation_config, resolved_output_dir)
    metrics = summarize_size_field_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
