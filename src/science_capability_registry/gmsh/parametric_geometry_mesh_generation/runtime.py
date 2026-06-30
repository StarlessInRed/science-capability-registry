"""Gmsh Python API runtime for C01."""

from __future__ import annotations

import json
import math
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import map_windows_path_to_wsl, run_wsl

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


def _summarize_mesh(gmsh: Any, dimension: int) -> dict[str, Any]:
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
    for element_type, element_tags, element_nodes in zip(*gmsh.model.mesh.getElements(dimension)):
        name, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
        element_count += len(element_tags)
        element_quality_tags.extend(int(tag) for tag in element_tags)
        if node_count >= 3 and "triangle" in name.lower():
            for offset in range(0, len(element_nodes), node_count):
                tags = [int(tag) for tag in element_nodes[offset : offset + 3]]
                if all(tag in node_map for tag in tags):
                    fallback_triangle_qualities.append(_triangle_quality([node_map[tag] for tag in tags]))

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
    if element_quality_tags:
        qualities = [float(value) for value in gmsh.model.mesh.getElementQualities(element_quality_tags)]
        quality_metric = "gmsh_minSICN"
    else:
        qualities = fallback_triangle_qualities
        quality_metric = "linear_triangle_quality_proxy"
    min_quality = min(qualities) if qualities else 1.0
    return {
        "node_count": len(node_tags),
        "element_count": element_count,
        "coordinates_finite": finite,
        "physical_groups": groups,
        "quality": {
            "metric": quality_metric,
            "sample_count": len(qualities),
            "min_quality_proxy": min_quality,
        },
    }


def _foam_list_count(path: Path) -> int | None:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _parse_boundary_names(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    names: list[str] = []
    inside_entries = False
    for index, line in enumerate(lines):
        stripped = line.strip().strip('"')
        if not inside_entries:
            if stripped == "(":
                inside_entries = True
            continue
        if stripped == ")":
            break
        if not re.match(r"^[A-Za-z0-9_./-]+$", stripped):
            continue
        next_tokens = [candidate.strip() for candidate in lines[index + 1 : index + 4] if candidate.strip()]
        if next_tokens and next_tokens[0] == "{":
            names.append(stripped)
    return names


def summarize_openfoam_polymesh(output_dir: Path, expected_outputs: list[str]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for rel_path in expected_outputs:
        path = output_dir / rel_path
        files[rel_path] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    poly_mesh = output_dir / "constant" / "polyMesh"
    counts = {}
    for name in ["points", "faces", "owner", "neighbour"]:
        path = poly_mesh / name
        counts[name] = _foam_list_count(path) if path.exists() else None

    boundary_path = poly_mesh / "boundary"
    boundary_names = _parse_boundary_names(boundary_path) if boundary_path.exists() else []
    return {
        "files": files,
        "counts": counts,
        "boundary_names": boundary_names,
        "structural_checks": {
            "has_points": isinstance(counts.get("points"), int) and counts["points"] > 0,
            "has_faces": isinstance(counts.get("faces"), int) and counts["faces"] > 0,
            "owner_matches_faces": counts.get("owner") == counts.get("faces") and isinstance(counts.get("faces"), int),
            "neighbour_not_larger_than_faces": (
                isinstance(counts.get("neighbour"), int)
                and isinstance(counts.get("faces"), int)
                and counts["neighbour"] <= counts["faces"]
            ),
        },
    }


def _write_openfoam_control_dict(output_dir: Path) -> Path:
    system_dir = output_dir / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    control_dict = system_dir / "controlDict"
    control_dict.write_text(
        "\n".join(
            [
                "FoamFile",
                "{",
                "    version     2.0;",
                "    format      ascii;",
                "    class       dictionary;",
                "    object      controlDict;",
                "}",
                "application     gmshToFoam;",
                "startFrom       startTime;",
                "startTime       0;",
                "stopAt          endTime;",
                "endTime         0;",
                "deltaT          1;",
                "writeControl    timeStep;",
                "writeInterval   1;",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "constant").mkdir(parents=True, exist_ok=True)
    return control_dict


def run_downstream_import(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    downstream = config.get("downstream_import") or {}
    if not downstream.get("enabled"):
        return {"enabled": False, "status": "not_configured"}

    poly_mesh_dir = output_dir / "constant" / "polyMesh"
    if poly_mesh_dir.exists():
        shutil.rmtree(poly_mesh_dir)
    _write_openfoam_control_dict(output_dir)

    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "log.gmshToFoam"
    timeout_s = float(downstream["timeout_s"])
    distro = downstream["wsl_distro"]
    bashrc_path = downstream["bashrc_path"]
    case_dir_linux = map_windows_path_to_wsl(output_dir, distro, timeout_s)
    command = downstream["command"]
    script = (
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
        f"cd {shlex.quote(case_dir_linux)}; "
        "command -v gmshToFoam >/dev/null 2>&1 || exit 127; "
        f"{command}"
    )
    result = run_wsl(distro, script, timeout_s)
    log_text = result.stdout
    if result.stderr:
        log_text += result.stderr
    log_path.write_text(log_text, encoding="utf-8")

    expected_outputs = list(downstream["expected_outputs"])
    poly_summary = summarize_openfoam_polymesh(output_dir, expected_outputs)
    expected_present = all(
        rel_path == "downstream_import_summary.json" or (item["exists"] and item["size_bytes"] > 0)
        for rel_path, item in poly_summary["files"].items()
    )
    required_boundaries = set(downstream["expected_boundary_names"])
    boundary_names = set(poly_summary["boundary_names"])
    structural_passed = all(poly_summary["structural_checks"].values())
    status = "passed" if result.returncode == 0 and expected_present and required_boundaries.issubset(boundary_names) and structural_passed else "failed"
    summary = {
        "enabled": True,
        "status": status,
        "engine": downstream["engine"],
        "runtime_profile": downstream["runtime_profile"],
        "command": command,
        "returncode": result.returncode,
        "log": str(log_path),
        "required_boundary_names": sorted(required_boundaries),
        "polyMesh": poly_summary,
    }
    summary_path = output_dir / "downstream_import_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if "downstream_import_summary.json" in summary["polyMesh"]["files"]:
        summary["polyMesh"]["files"]["downstream_import_summary.json"] = {
            "path": str(summary_path),
            "exists": True,
            "size_bytes": summary_path.stat().st_size,
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


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
        dimension = int(config["mesh"]["dimension"])
        gmsh.model.mesh.generate(dimension)
        gmsh.write(str(mesh_path))
        summary = _summarize_mesh(gmsh, dimension)
    finally:
        gmsh.finalize()

    summary["artifacts"] = {
        "case.geo": str(geo_path),
        "case.msh": str(mesh_path),
        "mesh_summary.json": str(output_dir / "mesh_summary.json"),
        "downstream_import_summary.json": str(output_dir / "downstream_import_summary.json"),
        "validation.json": str(output_dir / "validation.json"),
        "validation_report.md": str(output_dir / "validation_report.md"),
    }
    downstream_summary = run_downstream_import(config, output_dir)
    if downstream_summary.get("enabled"):
        summary["downstream_import"] = downstream_summary
    summary_path = output_dir / "mesh_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    validation = validate_mesh_summary(summary, config, output_dir)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_dir / "validation_report.md", config, summary, validation)
    return {"summary": summary, "validation": validation}
