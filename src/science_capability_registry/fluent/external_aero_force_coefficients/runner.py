"""Runner for Fluent C04 external-aero reference CSV parsing."""

from __future__ import annotations

import csv
import json
import math
import os
import zipfile
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from science_capability_registry.fluent.batch_smoke import (
    collect_mesh_metrics,
    execute_fluent,
    extract_zip_entries,
    fluent_path,
    write_journal,
)
from science_capability_registry.fluent.official_replay_manifest.zip_catalog import (
    inspect_zip_archive,
    summarize_entries,
)

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_C04_external_aero_force_coefficients.schema.json"


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


def _safe_float(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    if not math.isfinite(result):
        return None
    return result


def _numeric_ranges(rows: list[dict[str, str]], columns: list[str]) -> tuple[dict[str, dict[str, float]], int, list[str]]:
    ranges: dict[str, dict[str, float]] = {}
    finite_values = 0
    nonfinite_cells: list[str] = []
    for column in columns:
        values = []
        for row_index, row in enumerate(rows, start=1):
            value = _safe_float(row.get(column, ""))
            if value is None:
                nonfinite_cells.append(f"{row_index}:{column}")
            else:
                values.append(value)
                finite_values += 1
        if values:
            ranges[column] = {"min": min(values), "max": max(values)}
    return ranges, finite_values, nonfinite_cells


def _is_monotonic(values: list[float]) -> bool:
    return all(next_value >= value for value, next_value in zip(values, values[1:]))


def _trend_checks(reference: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    if reference["reference_role"] != "lift_curve":
        return {}
    aoa_values = [_safe_float(row[reference["required_columns"][0]]) for row in rows]
    cl_values = [_safe_float(row[reference["required_columns"][1]]) for row in rows]
    finite_aoa = [value for value in aoa_values if value is not None]
    finite_cl = [value for value in cl_values if value is not None]
    return {
        "aoa_monotonic_non_decreasing": _is_monotonic(finite_aoa),
        "cl_monotonic_non_decreasing": _is_monotonic(finite_cl),
        "cl_min": min(finite_cl) if finite_cl else None,
        "cl_max": max(finite_cl) if finite_cl else None,
    }


def _read_reference_table(archive: zipfile.ZipFile, reference: dict[str, Any]) -> dict[str, Any]:
    with archive.open(reference["entry_path"]) as raw:
        reader = csv.DictReader(TextIOWrapper(raw, encoding="utf-8-sig", errors="replace"))
        if reader.fieldnames is None:
            raise ValueError(f"Reference CSV has no header: {reference['entry_path']}")
        rows = [row for row in reader if any((value or "").strip() for value in row.values())]
    columns = [column.strip() for column in reader.fieldnames]
    normalized_rows = [{(key or "").strip(): value for key, value in row.items()} for row in rows]
    numeric_rows = []
    skipped_rows = []
    for row_index, row in enumerate(normalized_rows, start=1):
        if all(_safe_float(row.get(column, "")) is not None for column in reference["required_columns"]):
            numeric_rows.append(row)
        else:
            skipped_rows.append(row_index)
    ranges, finite_values, nonfinite_cells = _numeric_ranges(numeric_rows, reference["required_columns"])
    return {
        "reference_id": reference["reference_id"],
        "reference_role": reference["reference_role"],
        "entry_path": reference["entry_path"],
        "columns": columns,
        "required_columns": reference["required_columns"],
        "raw_row_count": len(normalized_rows),
        "row_count": len(numeric_rows),
        "skipped_non_numeric_row_count": len(skipped_rows),
        "skipped_non_numeric_rows": skipped_rows,
        "numeric_ranges": ranges,
        "finite_numeric_values": finite_values,
        "nonfinite_cells": nonfinite_cells,
        "trend_checks": _trend_checks(reference, numeric_rows),
    }


def _build_manifest(config: dict[str, Any], output_dir: Path, source_root: Path) -> dict[str, Any]:
    archive_path = source_root / config["source_package"]["rel_path"]
    entries = inspect_zip_archive(archive_path)
    summary = summarize_entries(entries)
    reference_tables = []
    error_message = ""
    archive_status = "readable"
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for reference in config["reference_csvs"]:
                reference_tables.append(_read_reference_table(archive, reference))
    except Exception as exc:
        archive_status = "unreadable"
        error_message = str(exc)
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
        "reference_tables": reference_tables,
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "runtime_smoke": config.get("runtime_smoke", {}),
        "scope": "read-only Fluent C04 aero reference parser; no archive extraction or solver execution"
        if config["backend"]["type"] == "reference_csv_parser"
        else "Fluent C04 aero case-read smoke; no force or Cp extraction",
    }


def _write_runtime_journal(config: dict[str, Any], output_dir: Path, case_path: Path, dry_run: bool) -> Path:
    case_text = case_path.as_posix() if dry_run else fluent_path(case_path)
    return write_journal(
        output_dir / config["runtime_smoke"]["journal_file"],
        [
            f'/file/read-case "{case_text}"',
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
    if not dry_run and backend_type == "reference_csv_parser":
        raise ValueError("Fluent C04 parser is read-only and uses dry_run=True.")
    if backend_type not in {"reference_csv_parser", "fluent_case_read_smoke"}:
        raise NotImplementedError(f"Fluent C04 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    c04_manifest = _build_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "aero_reference_manifest.json",
        "reference_tables.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    if backend_type == "fluent_case_read_smoke":
        archive_path = source_root / config["source_package"]["rel_path"]
        extracted = extract_zip_entries(archive_path, [config["runtime_smoke"]["case_entry"]], resolved_output_dir)
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
        c04_manifest["runtime_metrics"] = runtime_metrics
    c04_manifest["generated_files"] = generated_files
    (resolved_output_dir / "aero_reference_manifest.json").write_text(json.dumps(c04_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "reference_tables.json").write_text(
        json.dumps(c04_manifest["reference_tables"], indent=2),
        encoding="utf-8",
    )
    validation = validate_manifest(c04_manifest, config)
    metrics = summarize_metrics(c04_manifest, validation)
    c04_manifest["validation"] = validation
    c04_manifest["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "aero_reference_manifest": "aero_reference_manifest.json",
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": c04_manifest["scope"],
    }
    (resolved_output_dir / "aero_reference_manifest.json").write_text(json.dumps(c04_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(c04_manifest, config, resolved_output_dir)
    metrics = summarize_metrics(c04_manifest, validation)
    c04_manifest["validation"] = validation
    c04_manifest["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "aero_reference_manifest.json").write_text(json.dumps(c04_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
