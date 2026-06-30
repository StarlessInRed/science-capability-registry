"""Validation for Gmsh C01 artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _required_groups(config: dict[str, Any]) -> set[str]:
    return set(config["validation"]["required_physical_groups"])


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    backend = manifest.get("backend", {})
    generated_files = set(manifest.get("generated_files", []))
    group_names = {item["name"] for item in manifest.get("physical_groups", [])}
    required = _required_groups(config)

    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", json.dumps(backend, ensure_ascii=False))
    _check(
        checks,
        "geometry.family",
        manifest.get("geometry", {}).get("family") == config["geometry"]["family"],
        json.dumps(manifest.get("geometry", {}), ensure_ascii=False),
    )
    _check(checks, "physical_groups.required", required.issubset(group_names), f"groups={sorted(group_names)}, required={sorted(required)}")

    for rel_path in config["validation"]["required_generated_files"]:
        _check(checks, f"generated_file.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(checks, f"generated_file.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run Gmsh geometry script manifest",
        "checks": checks,
    }


def validate_mesh_summary(summary: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    required = _required_groups(config)
    groups = set(summary.get("physical_groups", {}))
    nodes = int(summary.get("node_count", 0))
    elements = int(summary.get("element_count", 0))
    quality = summary.get("quality", {})
    min_quality = quality.get("min_quality_proxy")
    coordinates_finite = summary.get("coordinates_finite")

    _check(checks, "physical_groups.required", required.issubset(groups), f"groups={sorted(groups)}, required={sorted(required)}")
    _check(checks, "mesh.node_count", nodes >= int(config["validation"]["min_node_count"]), f"node_count={nodes}")
    _check(checks, "mesh.element_count", elements >= int(config["validation"]["min_element_count"]), f"element_count={elements}")
    _check(checks, "mesh.coordinates_finite", coordinates_finite is True or not config["validation"]["require_coordinate_finiteness"], str(coordinates_finite))
    _check(
        checks,
        "mesh.quality_proxy",
        isinstance(min_quality, (int, float)) and math.isfinite(float(min_quality)) and float(min_quality) >= float(config["validation"]["min_quality_proxy"]),
        json.dumps(quality, ensure_ascii=False),
    )

    downstream = config.get("downstream_import") or {}
    if downstream.get("enabled"):
        import_summary = summary.get("downstream_import", {})
        poly_mesh = import_summary.get("polyMesh", {})
        files = poly_mesh.get("files", {})
        boundary_names = set(poly_mesh.get("boundary_names", []))
        expected_boundaries = set(downstream["expected_boundary_names"])
        structural_checks = poly_mesh.get("structural_checks", {})
        _check(checks, "downstream_import.status", import_summary.get("status") == "passed", json.dumps(import_summary, ensure_ascii=False))
        _check(
            checks,
            "downstream_import.boundary_names",
            expected_boundaries.issubset(boundary_names),
            f"boundaries={sorted(boundary_names)}, required={sorted(expected_boundaries)}",
        )
        for rel_path in downstream["expected_outputs"]:
            file_info = files.get(rel_path, {})
            path = Path(output_dir) / rel_path if output_dir is not None else Path(rel_path)
            _check(
                checks,
                f"downstream_import.artifact.{rel_path}",
                file_info.get("exists") is True and int(file_info.get("size_bytes", 0)) > 0 and (output_dir is None or path.exists()),
                json.dumps(file_info, ensure_ascii=False),
            )
        for name, passed in structural_checks.items():
            _check(checks, f"downstream_import.structure.{name}", passed is True, json.dumps(structural_checks, ensure_ascii=False))

    solve = config.get("downstream_solve") or {}
    if solve.get("enabled"):
        solve_summary = summary.get("downstream_solve", {})
        files = solve_summary.get("files", {})
        validation = solve["validation"]
        command_results = solve_summary.get("command_results", [])
        continuity_error = solve_summary.get("max_continuity_error")
        boundary_names = set(solve_summary.get("boundary_names", []))
        expected_boundaries = set(validation["required_boundary_names"])
        _check(checks, "downstream_solve.status", solve_summary.get("status") == "passed", json.dumps(solve_summary, ensure_ascii=False))
        _check(
            checks,
            "downstream_solve.returncodes",
            bool(command_results) and all(item.get("returncode") == 0 for item in command_results),
            json.dumps(command_results, ensure_ascii=False),
        )
        _check(
            checks,
            "downstream_solve.boundary_names",
            expected_boundaries.issubset(boundary_names),
            f"boundaries={sorted(boundary_names)}, required={sorted(expected_boundaries)}",
        )
        _check(
            checks,
            "downstream_solve.check_mesh_ok",
            solve_summary.get("check_mesh_ok") is True or not validation["require_check_mesh_ok"],
            json.dumps(solve_summary, ensure_ascii=False),
        )
        _check(
            checks,
            "downstream_solve.potentialFoam_completed",
            solve_summary.get("potentialFoam_completed") is True,
            json.dumps(solve_summary, ensure_ascii=False),
        )
        _check(
            checks,
            "downstream_solve.max_continuity_error",
            (
                isinstance(continuity_error, (int, float))
                and math.isfinite(float(continuity_error))
                and float(continuity_error) <= float(validation["max_continuity_error"])
            ),
            f"max_continuity_error={continuity_error}",
        )
        _check(
            checks,
            "downstream_solve.no_fatal_error",
            solve_summary.get("fatal_error_detected") is False,
            json.dumps(solve_summary, ensure_ascii=False),
        )
        for rel_path in solve["expected_outputs"]:
            file_info = files.get(rel_path, {})
            path = Path(output_dir) / rel_path if output_dir is not None else Path(rel_path)
            _check(
                checks,
                f"downstream_solve.artifact.{rel_path}",
                file_info.get("exists") is True and int(file_info.get("size_bytes", 0)) > 0 and (output_dir is None or path.exists()),
                json.dumps(file_info, ensure_ascii=False),
            )

    if output_dir is not None:
        for rel_path in config["outputs"]["expected_outputs"]:
            if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
                continue
            path = Path(output_dir) / rel_path
            _check(checks, f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh Python API mesh generation summary",
        "checks": checks,
    }
