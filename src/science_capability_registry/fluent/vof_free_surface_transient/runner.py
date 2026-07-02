"""Runner for Fluent C05 VOF source setup."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from science_capability_registry.fluent.batch_smoke import (
    collect_mesh_metrics,
    execute_fluent,
    extract_zip_entries,
    fluent_path,
    write_journal,
)
from science_capability_registry.fluent.official_replay_manifest.zip_catalog import inspect_zip_archive, summarize_entries

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_C05_vof_free_surface_transient.schema.json"


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


def _build_manifest(config: dict[str, Any], output_dir: Path, source_root: Path) -> dict[str, Any]:
    archive_path = source_root / config["source_package"]["rel_path"]
    entries = []
    archive_status = "readable"
    error_message = ""
    try:
        entries = inspect_zip_archive(archive_path)
    except Exception as exc:
        archive_status = "unreadable"
        error_message = str(exc)
    summary = summarize_entries(entries)
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
        "source_package": config["source_package"],
        "setup_scope": config["setup_scope"],
        "archive": {
            "source_id": config["source_package"]["source_id"],
            "rel_path": config["source_package"]["rel_path"],
            "archive_status": archive_status,
            "error_message": error_message,
            "entry_count": summary["entry_count"],
            "entry_kind_counts": summary["entry_kind_counts"],
            "entrypoint_class": summary["entrypoint_class"],
        },
        "entries": entries,
        "mesh_entries": mesh_entries,
        "mesh_format_counts": _mesh_format_counts(mesh_entries),
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "runtime_smoke": config.get("runtime_smoke", {}),
        "scope": "read-only Fluent C05 VOF source setup manifest; no archive extraction or solver execution"
        if config["backend"]["type"] == "mesh_setup_manifest"
        else "Fluent C05 VOF source mesh-read smoke; no VOF solver execution",
    }


def _write_runtime_journal(config: dict[str, Any], output_dir: Path, mesh_path: Path, dry_run: bool) -> Path:
    mesh_text = mesh_path.as_posix() if dry_run else fluent_path(mesh_path)
    return write_journal(
        output_dir / config["runtime_smoke"]["journal_file"],
        [
            f'/file/read-case "{mesh_text}"',
            "/mesh/check",
            "/exit yes",
        ],
    )


def _write_dry_run_placeholders(output_dir: Path) -> None:
    placeholder = "dry-run placeholder; Fluent was not executed for this artifact.\n"
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        (output_dir / name).write_text(placeholder, encoding="utf-8")


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
    backend_type = config["backend"]["type"]
    if not dry_run and backend_type == "mesh_setup_manifest":
        raise ValueError("Fluent C05 source setup manifest is read-only and uses dry_run=True.")
    if backend_type not in {"mesh_setup_manifest", "fluent_mesh_read_smoke"}:
        raise NotImplementedError(f"Fluent C05 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    setup_manifest = _build_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "vof_setup_manifest.json",
        "mesh_entries.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    if backend_type == "fluent_mesh_read_smoke":
        archive_path = source_root / config["source_package"]["rel_path"]
        extracted = extract_zip_entries(archive_path, [config["runtime_smoke"]["mesh_entry"]], resolved_output_dir)
        journal_path = _write_runtime_journal(config, resolved_output_dir, extracted[0], dry_run)
        generated_files.extend([extracted[0].name, journal_path.name, "stdout.txt", "stderr.txt", "transcript.txt"])
        if dry_run:
            _write_dry_run_placeholders(resolved_output_dir)
            runtime_metrics = {
                "fluent_return_code": None,
                "mesh_cell_count": None,
                "mesh_face_counts": {},
                "mesh_check_completed": False,
                "fluent_warning_count": 0,
                "fluent_error_count": 0,
                "runtime_status": "dry_run_not_executed",
            }
        else:
            runtime_metrics = collect_mesh_metrics(
                resolved_output_dir,
                execute_fluent(config, resolved_output_dir, journal_path),
            )
        setup_manifest["runtime_metrics"] = runtime_metrics
    setup_manifest["generated_files"] = generated_files
    (resolved_output_dir / "vof_setup_manifest.json").write_text(json.dumps(setup_manifest, indent=2), encoding="utf-8")
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
        "setup_manifest": "vof_setup_manifest.json",
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
    (resolved_output_dir / "vof_setup_manifest.json").write_text(json.dumps(setup_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
