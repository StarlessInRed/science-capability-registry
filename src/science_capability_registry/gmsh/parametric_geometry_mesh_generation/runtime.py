"""Gmsh Python API runtime for C01."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .report import write_validation_report
from .validation import validate_mesh_summary


def _import_gmsh() -> Any:
    try:
        import gmsh
    except ModuleNotFoundError as exc:
        raise RuntimeError("The gmsh Python package is required for backend.type=python_api.") from exc
    return gmsh


def _triangle_quality(points: list[tuple[float, float, float]]) -> float:
    a = math.dist(points[0], points[1])
    b = math.dist(points[1], points[2])
    c = math.dist(points[2], points[0])
    semiperimeter = 0.5 * (a + b + c)
    area_square = semiperimeter * (semiperimeter - a) * (semiperimeter - b) * (semiperimeter - c)
    if area_square <= 0.0:
        return 0.0
    area = math.sqrt(area_square)
    denominator = a * a + b * b + c * c
    if denominator <= 0.0:
        return 0.0
    return 4.0 * math.sqrt(3.0) * area / denominator


def _summarize_mesh(gmsh: Any) -> dict[str, Any]:
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    node_map: dict[int, tuple[float, float, float]] = {}
    finite = True
    for index, tag in enumerate(node_tags):
        point = (float(coords[3 * index]), float(coords[3 * index + 1]), float(coords[3 * index + 2]))
        finite = finite and all(math.isfinite(value) for value in point)
        node_map[int(tag)] = point

    element_count = 0
    qualities: list[float] = []
    for element_type, element_tags, element_nodes in zip(*gmsh.model.mesh.getElements(2)):
        name, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
        element_count += len(element_tags)
        if node_count >= 3 and "triangle" in name.lower():
            for offset in range(0, len(element_nodes), node_count):
                tags = [int(tag) for tag in element_nodes[offset : offset + 3]]
                if all(tag in node_map for tag in tags):
                    qualities.append(_triangle_quality([node_map[tag] for tag in tags]))

    groups: dict[str, dict[str, Any]] = {}
    for dimension, tag in gmsh.model.getPhysicalGroups():
        name = gmsh.model.getPhysicalName(dimension, tag)
        entities = gmsh.model.getEntitiesForPhysicalGroup(dimension, tag)
        groups[name] = {
            "dimension": int(dimension),
            "tag": int(tag),
            "entity_count": len(entities),
            "entities": [int(entity) for entity in entities],
        }
    min_quality = min(qualities) if qualities else 1.0
    return {
        "node_count": len(node_tags),
        "element_count": element_count,
        "coordinates_finite": finite,
        "physical_groups": groups,
        "quality": {
            "metric": "linear_triangle_quality_proxy",
            "sample_count": len(qualities),
            "min_quality_proxy": min_quality,
        },
    }


def generate_mesh(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    gmsh = _import_gmsh()
    geo_path = output_dir / "case.geo"
    mesh_path = output_dir / "case.msh"
    gmsh.initialize()
    try:
        gmsh.open(str(geo_path))
        gmsh.option.setNumber("Mesh.ElementOrder", int(config["mesh"]["element_order"]))
        gmsh.option.setNumber("Mesh.Algorithm", int(config["mesh"]["algorithm"]))
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2 if config["mesh"]["output_format"] == "msh2" else 4.1)
        gmsh.model.mesh.generate(int(config["mesh"]["dimension"]))
        gmsh.write(str(mesh_path))
        summary = _summarize_mesh(gmsh)
    finally:
        gmsh.finalize()

    summary["artifacts"] = {
        "case.geo": str(geo_path),
        "case.msh": str(mesh_path),
        "mesh_summary.json": str(output_dir / "mesh_summary.json"),
        "validation.json": str(output_dir / "validation.json"),
        "validation_report.md": str(output_dir / "validation_report.md"),
    }
    summary_path = output_dir / "mesh_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    validation = validate_mesh_summary(summary, config, output_dir)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_dir / "validation_report.md", config, summary, validation)
    return {"summary": summary, "validation": validation}
