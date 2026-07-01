"""Runner for Gmsh C04 CAD import and healing contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_cad_healing_metrics, validate_manifest

SCHEMA_ID = "schemas/gmsh_C04_cad_import_geometry_healing.schema.json"


def _write_cad_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cad_import_manifest = {
        "cad_source": config["cad_source"],
        "healing_operations": config["healing_operations"],
        "scope": "static contract only; no CAD file imported",
    }
    entity_map = {
        "entity_map_expectations": config["entity_map_expectations"],
        "physical_group_rebinding": config["physical_group_rebinding"],
    }
    healing_report = {
        "enabled_operations": [item for item in config["healing_operations"] if item["enabled"]],
        "modified_entity_count": config["entity_map_expectations"]["modified_entity_count"],
        "deleted_entity_count": config["entity_map_expectations"]["deleted_entity_count"],
        "new_entity_count": config["entity_map_expectations"]["new_entity_count"],
    }
    meshability_summary = {
        "meshability_thresholds": config["meshability_thresholds"],
        "unassigned_entity_count": config["physical_group_rebinding"]["unassigned_entity_count"],
        "duplicate_or_sliver_count": config["physical_group_rebinding"]["duplicate_or_sliver_count"],
    }
    (output_dir / "cad_import_manifest.json").write_text(json.dumps(cad_import_manifest, indent=2), encoding="utf-8")
    (output_dir / "entity_map.json").write_text(json.dumps(entity_map, indent=2), encoding="utf-8")
    (output_dir / "healing_report.json").write_text(json.dumps(healing_report, indent=2), encoding="utf-8")
    (output_dir / "meshability_summary.json").write_text(json.dumps(meshability_summary, indent=2), encoding="utf-8")
    return ["cad_import_manifest.json", "entity_map.json", "healing_report.json", "meshability_summary.json"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "cad_source": config["cad_source"],
        "healing_operations": config["healing_operations"],
        "entity_map_expectations": config["entity_map_expectations"],
        "physical_group_rebinding": config["physical_group_rebinding"],
        "meshability_thresholds": config["meshability_thresholds"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build cad_import_manifest.json",
            "static-contract:build entity_map.json",
            "static-contract:build healing_report.json",
            "static-contract:build meshability_summary.json",
        ],
        "scope": "static CAD healing contract; no OpenCASCADE import or mesh generation",
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
        raise ValueError("Gmsh C04 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Gmsh C04 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_cad_artifacts(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, config)
    metrics = summarize_cad_healing_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, config, resolved_output_dir)
    metrics = summarize_cad_healing_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
