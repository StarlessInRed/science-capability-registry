"""Runner for Fluent C06 sliding/rotating mesh source setup."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from science_capability_registry.fluent.official_replay_manifest.zip_catalog import inspect_zip_archive, summarize_entries

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_C06_sliding_rotating_mesh.schema.json"


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


def _mesh_format_counts(mesh_entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in mesh_entries:
        suffix = entry["compound_extension"]
        counts[suffix] = counts.get(suffix, 0) + 1
    return counts


def _inspect_package(source_root: Path, source: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    archive_path = source_root / source["rel_path"]
    entries = []
    archive_status = "readable"
    error_message = ""
    try:
        entries = inspect_zip_archive(archive_path)
    except Exception as exc:
        archive_status = "unreadable"
        error_message = str(exc)
    summary = summarize_entries(entries)
    package = {
        "source_id": source["source_id"],
        "source_role": source["source_role"],
        "rel_path": source["rel_path"],
        "archive_status": archive_status,
        "error_message": error_message,
        "entry_count": summary["entry_count"],
        "entry_kind_counts": summary["entry_kind_counts"],
        "entrypoint_class": summary["entrypoint_class"],
    }
    scoped_entries = [{**entry, "source_id": source["source_id"]} for entry in entries]
    return package, scoped_entries


def _build_manifest(config: dict[str, Any], output_dir: Path, source_root: Path) -> dict[str, Any]:
    packages = []
    entries = []
    for source in config["source_packages"]:
        package, scoped_entries = _inspect_package(source_root, source)
        packages.append(package)
        entries.extend(scoped_entries)
    mesh_entries = [entry for entry in entries if entry["entry_kind"] == "mesh"]
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
        "source_packages": config["source_packages"],
        "setup_scope": config["setup_scope"],
        "packages": packages,
        "entries": entries,
        "mesh_entries": mesh_entries,
        "mesh_format_counts": _mesh_format_counts(mesh_entries),
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "scope": "read-only Fluent C06 sliding/rotating mesh source manifest; no archive extraction or solver execution",
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
        raise ValueError("Fluent C06 source setup is read-only and uses dry_run=True.")
    if config["backend"]["type"] != "mesh_setup_manifest":
        raise NotImplementedError(f"Fluent C06 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    setup_manifest = _build_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "rotating_mesh_setup_manifest.json",
        "mesh_entries.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    setup_manifest["generated_files"] = generated_files
    (resolved_output_dir / "rotating_mesh_setup_manifest.json").write_text(json.dumps(setup_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "mesh_entries.json").write_text(json.dumps(setup_manifest["mesh_entries"], indent=2), encoding="utf-8")
    validation = validate_manifest(setup_manifest, config)
    metrics = summarize_metrics(setup_manifest, validation)
    setup_manifest["validation"] = validation
    setup_manifest["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "setup_manifest": "rotating_mesh_setup_manifest.json",
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": setup_manifest["scope"],
    }
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(setup_manifest, config, resolved_output_dir)
    metrics = summarize_metrics(setup_manifest, validation)
    setup_manifest["validation"] = validation
    setup_manifest["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "rotating_mesh_setup_manifest.json").write_text(json.dumps(setup_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
