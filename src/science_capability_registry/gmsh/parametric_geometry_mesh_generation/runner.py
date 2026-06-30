"""Runner for Gmsh C01 parametric geometry and mesh generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import generate_mesh
from .validation import validate_manifest


def _physical_group_lookup(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["role"]: item for item in config["physical_groups"]}


def _geo_text(config: dict[str, Any]) -> str:
    geometry = config["geometry"]
    groups = _physical_group_lookup(config)
    x0, y0 = geometry["origin_m"]
    length = float(geometry["length_m"])
    height = float(geometry["height_m"])
    lc = float(geometry["characteristic_length_m"])
    x1 = float(x0) + length
    y1 = float(y0) + height
    base = (
        'SetFactory("Built-in");\n'
        f"lc = {lc:g};\n"
        f"Point(1) = {{{float(x0):g}, {float(y0):g}, 0, lc}};\n"
        f"Point(2) = {{{x1:g}, {float(y0):g}, 0, lc}};\n"
        f"Point(3) = {{{x1:g}, {y1:g}, 0, lc}};\n"
        f"Point(4) = {{{float(x0):g}, {y1:g}, 0, lc}};\n"
        "Line(1) = {1, 2};\n"
        "Line(2) = {2, 3};\n"
        "Line(3) = {3, 4};\n"
        "Line(4) = {4, 1};\n"
        "Curve Loop(1) = {1, 2, 3, 4};\n"
        "Plane Surface(1) = {1};\n"
    )
    if geometry["family"] == "rectangle_channel_2d":
        physical_groups = (
            f'Physical Curve("{groups["inlet"]["name"]}") = {{4}};\n'
            f'Physical Curve("{groups["outlet"]["name"]}") = {{2}};\n'
            f'Physical Curve("{groups["wall"]["name"]}") = {{1, 3}};\n'
            f'Physical Surface("{groups["domain"]["name"]}") = {{1}};\n'
        )
    elif geometry["family"] == "extruded_rectangle_channel_3d":
        thickness = float(geometry["thickness_m"])
        physical_groups = (
            f"out[] = Extrude {{0, 0, {thickness:g}}} {{ Surface{{1}}; Layers{{1}}; }};\n"
            f'Physical Surface("{groups["front_back"]["name"]}") = {{1, out[0]}};\n'
            f'Physical Surface("{groups["wall"]["name"]}") = {{out[2], out[4]}};\n'
            f'Physical Surface("{groups["outlet"]["name"]}") = {{out[3]}};\n'
            f'Physical Surface("{groups["inlet"]["name"]}") = {{out[5]}};\n'
            f'Physical Volume("{groups["domain"]["name"]}") = {{out[1]}};\n'
        )
    else:
        raise ValueError(f"Unsupported Gmsh geometry family: {geometry['family']!r}")
    mesh_options = (
        f"Mesh.ElementOrder = {int(config['mesh']['element_order'])};\n"
        f"Mesh.Algorithm = {int(config['mesh']['algorithm'])};\n"
        f"Mesh.MshFileVersion = {2.2 if config['mesh']['output_format'] == 'msh2' else 4.1};\n"
    )
    return base + physical_groups + mesh_options


def _write_geo(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    geo_path = output_dir / "case.geo"
    geo_path.write_text(_geo_text(config), encoding="utf-8")
    return ["case.geo"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/gmsh_C01_parametric_geometry_mesh_generation.schema.json",
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "geometry": config["geometry"],
        "physical_groups": config["physical_groups"],
        "mesh": config["mesh"],
        "downstream_import": config.get("downstream_import", {"enabled": False}),
        "generated_files": generated_files,
        "runtime_commands": ["gmsh-python:open case.geo", "gmsh-python:model.mesh.generate"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": "dry-run geometry script generation; no mesh generated",
    }


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
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

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_geo(resolved_output_dir, config)
    manifest = _build_manifest(config, resolved_output_dir, generated_files)

    if dry_run:
        validation = validate_manifest(manifest, config, resolved_output_dir)
        manifest["validation"] = validation
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("Gmsh C01 dry_run_only backend requires dry_run=True.")
    if backend_type != "python_api":
        raise NotImplementedError(f"Gmsh C01 backend {backend_type!r} is not implemented.")

    runtime = generate_mesh(config, resolved_output_dir)
    manifest["scope"] = "Gmsh Python API geometry and mesh generation"
    runtime_generated = {*generated_files, "case.msh", "mesh_summary.json"}
    downstream = runtime["summary"].get("downstream_import", {})
    if downstream.get("enabled"):
        runtime_generated.update(
            rel_path
            for rel_path, file_info in downstream.get("polyMesh", {}).get("files", {}).items()
            if file_info.get("exists")
        )
    manifest["generated_files"] = sorted(runtime_generated)
    manifest["runtime"] = runtime["summary"]
    manifest["validation"] = runtime["validation"]
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
