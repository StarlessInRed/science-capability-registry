"""Runner for Fluent official replay source manifests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .bindings import bindings_with_source_summaries
from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_manifest_metrics, validate_manifest
from .zip_catalog import inspect_directory, inspect_reference_file, inspect_zip_archive, summarize_entries

SCHEMA_ID = "schemas/fluent_official_replay_manifest.schema.json"


def _source_root(config: dict[str, Any], require_exists: bool) -> Path:
    env_name = config["source_root"]["source_root_env"]
    value = os.environ.get(env_name)
    if not value:
        if require_exists:
            raise ValueError(f"Missing required environment variable {env_name} for Fluent source root.")
        return Path(f"${env_name}")
    path = Path(value)
    if require_exists and not path.exists():
        raise FileNotFoundError(f"Fluent source root from {env_name} does not exist: {path}")
    return path


def _inspect_source_package(source_root: Path, source: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = source_root / source["rel_path"]
    entries: list[dict[str, Any]] = []
    archive_status = "readable"
    error_message = ""
    try:
        if source["source_kind"] == "zip_archive":
            entries = inspect_zip_archive(path)
        elif source["source_kind"] == "legacy_directory":
            entries = inspect_directory(path)
        elif source["source_kind"] == "reference_file":
            entries = inspect_reference_file(path)
        else:
            raise NotImplementedError(f"Unsupported source_kind {source['source_kind']!r}")
    except Exception as exc:
        archive_status = "unreadable"
        error_message = str(exc)
    summary = summarize_entries(entries)
    present_classes = set(summary["entry_kind_counts"])
    missing_expected = [entry_class for entry_class in source["expected_entry_classes"] if entry_class not in present_classes]
    package = {
        **source,
        "logical_source_path": f"{source_root.as_posix()}/{source['rel_path']}",
        "archive_status": archive_status,
        "error_message": error_message,
        "summary": summary,
        "missing_expected_entry_classes": missing_expected,
    }
    scoped_entries = [{**entry, "source_id": source["source_id"], "seed_id": source["seed_id"]} for entry in entries]
    return package, scoped_entries


def _build_official_manifest(config: dict[str, Any], output_dir: Path, source_root: Path) -> dict[str, Any]:
    packages = []
    entries = []
    package_summaries: dict[str, dict[str, Any]] = {}
    for source in config["source_packages"]:
        package, package_entries = _inspect_source_package(source_root, source)
        packages.append(package)
        entries.extend(package_entries)
        package_summaries[source["source_id"]] = package
    capability_bindings = bindings_with_source_summaries(config, package_summaries)
    return {
        "schema_id": SCHEMA_ID,
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "validated_config": True,
        "output_dir": str(output_dir),
        "source_root": {
            "logical_path": config["source_root"]["logical_path"],
            "source_root_env": config["source_root"]["source_root_env"],
        },
        "backend": config["backend"],
        "packages": packages,
        "entries": entries,
        "capability_bindings": capability_bindings,
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "scope": "read-only Fluent source package manifest; no archive extraction or solver execution",
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
        raise ValueError("Fluent official replay manifest is read-only and uses dry_run=True.")
    if config["backend"]["type"] != "archive_manifest":
        raise NotImplementedError(f"Fluent official replay manifest backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    official_manifest = _build_official_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "official_replay_manifest.json",
        "source_entries.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    official_manifest["generated_files"] = generated_files
    (resolved_output_dir / "official_replay_manifest.json").write_text(
        json.dumps(official_manifest, indent=2),
        encoding="utf-8",
    )
    (resolved_output_dir / "source_entries.json").write_text(
        json.dumps(official_manifest["entries"], indent=2),
        encoding="utf-8",
    )
    validation = validate_manifest(official_manifest, config)
    metrics = summarize_manifest_metrics(official_manifest, validation)
    official_manifest["validation"] = validation
    official_manifest["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "official_replay_manifest": "official_replay_manifest.json",
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": official_manifest["scope"],
    }
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(official_manifest, config, resolved_output_dir)
    metrics = summarize_manifest_metrics(official_manifest, validation)
    official_manifest["validation"] = validation
    official_manifest["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "official_replay_manifest.json").write_text(
        json.dumps(official_manifest, indent=2),
        encoding="utf-8",
    )
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
