"""Runner for Fluent C02 verification reference mapping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_reference_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_C02_verification_reference_validation.schema.json"


def _reference_manifest(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "reference_source": config["reference_source"],
        "governing_model": config["governing_model"],
        "geometry": config["geometry"],
        "material_properties": config["material_properties"],
        "boundary_conditions": config["boundary_conditions"],
        "reference_formula": config["reference_formula"],
        "reference_values": config["reference_values"],
        "sampling_policy": config["sampling_policy"],
        "validation_targets": {
            "max_manual_relative_error": config["validation"]["max_manual_relative_error"],
        },
        "scope": "verification-manual static reference mapping; no Fluent execution",
    }


def _write_reference_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reference_manifest.json").write_text(
        json.dumps(_reference_manifest(config), indent=2),
        encoding="utf-8",
    )
    return ["reference_manifest.json"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    reference_manifest = _reference_manifest(config)
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(output_dir),
        "fluent": config["fluent"],
        "backend": config["backend"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "runtime_commands": [
            "static-contract:build reference_manifest.json",
            "static-contract:validate manual target table",
        ],
        "scope": "Fluent C02 verification reference static-readiness",
        **reference_manifest,
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
        raise ValueError("Fluent C02 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Fluent C02 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_reference_artifacts(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, config)
    metrics = summarize_reference_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, config, resolved_output_dir)
    metrics = summarize_reference_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
