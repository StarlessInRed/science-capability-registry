"""Small Gmsh mesh-summary helpers for runtime smoke gates."""

from __future__ import annotations

import math
from typing import Any


def import_gmsh() -> Any:
    try:
        import gmsh
    except ModuleNotFoundError as exc:
        raise RuntimeError("The gmsh Python package is required for backend.type=python_api.") from exc
    return gmsh


def triangle_quality(points: list[tuple[float, float, float]]) -> float:
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


def triangle_aspect_ratio(points: list[tuple[float, float, float]]) -> float:
    lengths = [
        math.dist(points[0], points[1]),
        math.dist(points[1], points[2]),
        math.dist(points[2], points[0]),
    ]
    shortest = min(lengths)
    if shortest <= 0.0:
        return float("inf")
    return max(lengths) / shortest


def summarize_current_mesh(gmsh: Any, dimension: int) -> dict[str, Any]:
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    node_map: dict[int, tuple[float, float, float]] = {}
    finite = True
    for index, tag in enumerate(node_tags):
        point = (float(coords[3 * index]), float(coords[3 * index + 1]), float(coords[3 * index + 2]))
        finite = finite and all(math.isfinite(value) for value in point)
        node_map[int(tag)] = point

    element_count = 0
    element_quality_tags: list[int] = []
    fallback_triangle_qualities: list[float] = []
    fallback_aspect_ratios: list[float] = []
    for element_type, element_tags, element_nodes in zip(*gmsh.model.mesh.getElements(dimension)):
        name, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
        element_count += len(element_tags)
        element_quality_tags.extend(int(tag) for tag in element_tags)
        if node_count >= 3 and "triangle" in name.lower():
            for offset in range(0, len(element_nodes), node_count):
                tags = [int(tag) for tag in element_nodes[offset : offset + 3]]
                if all(tag in node_map for tag in tags):
                    points = [node_map[tag] for tag in tags]
                    fallback_triangle_qualities.append(triangle_quality(points))
                    fallback_aspect_ratios.append(triangle_aspect_ratio(points))

    groups: dict[str, dict[str, Any]] = {}
    for group_dimension, tag in gmsh.model.getPhysicalGroups():
        name = gmsh.model.getPhysicalName(group_dimension, tag)
        entities = gmsh.model.getEntitiesForPhysicalGroup(group_dimension, tag)
        groups[name] = {
            "dimension": int(group_dimension),
            "tag": int(tag),
            "entity_count": len(entities),
            "entities": [int(entity) for entity in entities],
        }
    if element_quality_tags:
        qualities = [float(value) for value in gmsh.model.mesh.getElementQualities(element_quality_tags)]
        quality_metric = "gmsh_minSICN"
    else:
        qualities = fallback_triangle_qualities
        quality_metric = "linear_triangle_quality_proxy"
    min_quality = min(qualities) if qualities else 1.0
    max_aspect_ratio = max(fallback_aspect_ratios) if fallback_aspect_ratios else None
    return {
        "node_count": len(node_tags),
        "element_count": element_count,
        "coordinates_finite": finite,
        "physical_groups": groups,
        "quality": {
            "metric": quality_metric,
            "sample_count": len(qualities),
            "min_quality_proxy": min_quality,
            "max_aspect_ratio_proxy": max_aspect_ratio,
        },
    }
