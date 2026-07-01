"""Runner for Gmsh C06 multi-solver export contracts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_export_metrics, validate_manifest

SCHEMA_ID = "schemas/gmsh_C06_multi_solver_mesh_export_contract.schema.json"


def _write_export_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    export_manifest = {
        "source_mesh": config["source_mesh"],
        "unit_policy": config["unit_policy"],
        "orientation_policy": config["orientation_policy"],
        "export_targets": config["export_targets"],
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(export_manifest, indent=2), encoding="utf-8")
    with (output_dir / "format_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_id",
                "solver_family",
                "target_solver",
                "export_format",
                "contract_status",
                "expected_boundary_names",
                "expected_element_count_min",
                "max_element_count_delta_fraction",
            ],
        )
        writer.writeheader()
        for target in config["export_targets"]:
            writer.writerow(
                {
                    **target,
                    "expected_boundary_names": "|".join(target["expected_boundary_names"]),
                }
            )
    import_summary = {
        "status": "static_contract_only",
        "successful_import_count": 0,
        "targets": config["export_targets"],
        "scope": "no downstream import commands executed",
    }
    (output_dir / "solver_import_summary.json").write_text(json.dumps(import_summary, indent=2), encoding="utf-8")
    return ["export_manifest.json", "format_matrix.csv", "solver_import_summary.json"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "source_mesh": config["source_mesh"],
        "unit_policy": config["unit_policy"],
        "orientation_policy": config["orientation_policy"],
        "export_targets": config["export_targets"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build export_manifest.json",
            "static-contract:build format_matrix.csv",
            "static-contract:build solver_import_summary.json",
        ],
        "scope": "static multi-solver export contract; no import command execution",
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
        raise ValueError("Gmsh C06 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Gmsh C06 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_export_artifacts(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, config)
    metrics = summarize_export_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, config, resolved_output_dir)
    metrics = summarize_export_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
