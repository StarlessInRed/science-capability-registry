"""Runner for Fluent seed-suite static readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_suite_config, repo_relative_path, validate_suite_config
from .report import write_validation_report
from .validation import summarize_seed_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_seed_suite.schema.json"


def _seed_case_summary(config: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = []
    for seed in config["seed_cases"]:
        summaries.append(
            {
                "seed_id": seed["seed_id"],
                "asset_path": seed["asset_path"],
                "capability_slug": seed["capability_slug"],
                "benchmark_status": seed["benchmark_status"],
                "benchmark_source": seed["benchmark_source"],
                "replay_paths": seed["replay_paths"],
                "validation_criteria": seed["validation_criteria"],
                "risks": seed["risks"],
            }
        )
    return summaries


def _write_seed_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_cases = _seed_case_summary(config)
    (output_dir / "seed_cases.json").write_text(json.dumps(seed_cases, indent=2), encoding="utf-8")
    return ["seed_cases.json"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(output_dir),
        "fluent": config["fluent"],
        "backend": config["backend"],
        "source_library": config["source_library"],
        "learning_loop": config["learning_loop"],
        "seed_cases": _seed_case_summary(config),
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:validate Fluent seed suite",
            "static-contract:write seed_cases.json",
        ],
        "scope": "static Fluent seed-suite contract; no solver execution",
    }


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_suite_config(config_path)
    else:
        config = validate_suite_config(config)

    if not dry_run:
        raise ValueError("Fluent seed suite currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Fluent seed-suite backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    generated_files = _write_seed_artifacts(resolved_output_dir, config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "seed_suite_manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, config)
    metrics = summarize_seed_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "seed_suite_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, config, resolved_output_dir)
    metrics = summarize_seed_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "seed_suite_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
