"""Runner for Gmsh C05 boundary-layer and size-field contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_size_field_metrics, validate_manifest

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

    if not dry_run:
        raise ValueError("Gmsh C05 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Gmsh C05 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_size_field_artifacts(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, config)
    metrics = summarize_size_field_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, config, resolved_output_dir)
    metrics = summarize_size_field_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
