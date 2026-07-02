"""Runner for Fluent C07 heat-transfer source readiness."""

from __future__ import annotations

import json
import os
import re
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

SCHEMA_ID = "schemas/fluent_C07_heat_transfer_energy_balance.schema.json"
FLOAT_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


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


def _case_data_key(entry_path: str) -> str:
    name = Path(entry_path).name
    for suffix in (".cas.h5", ".dat.h5", ".cas", ".dat"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _case_data_pairs(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    cases = { _case_data_key(entry["entry_path"]): entry["entry_path"] for entry in entries if entry["entry_kind"] == "case" }
    data = { _case_data_key(entry["entry_path"]): entry["entry_path"] for entry in entries if entry["entry_kind"] == "data" }
    pairs = []
    for key in sorted(set(cases) & set(data)):
        pairs.append({"pair_id": key, "case_entry": cases[key], "data_entry": data[key]})
    return pairs


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
        "thermal_scope": config["thermal_scope"],
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
        "case_data_pairs": _case_data_pairs(entries),
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "runtime_smoke": config.get("runtime_smoke", {}),
        "scope": "read-only Fluent C07 heat-transfer source manifest; no archive extraction or solver execution"
        if config["backend"]["type"] == "case_data_manifest"
        else "Fluent C07 heat-transfer case/data read smoke with temperature and heat-transfer report extraction",
    }


def _thermal_report_lines(config: dict[str, Any]) -> list[str]:
    reports = config["runtime_smoke"].get("thermal_reports")
    if reports is None:
        return []
    cell_zone = reports["cell_zone"]
    lines = [
        "/report/volume-integrals/minimum",
        cell_zone,
        "()",
        "temperature",
        "no",
        "/report/volume-integrals/maximum",
        cell_zone,
        "()",
        "temperature",
        "no",
    ]
    for surface in reports["temperature_surfaces"]:
        lines.extend(
            [
                "/report/surface-integrals/area-weighted-avg",
                surface,
                "()",
                "temperature",
                "no",
            ]
        )
    if reports["heat_transfer_flux_all_boundaries"]:
        lines.extend(["/report/fluxes/heat-transfer", "yes", "no"])
    return lines


def _write_runtime_journal(config: dict[str, Any], output_dir: Path, case_path: Path, dry_run: bool) -> Path:
    case_text = case_path.as_posix() if dry_run else fluent_path(case_path)
    return write_journal(
        output_dir / config["runtime_smoke"]["journal_file"],
        [
            f'/file/read-case-data "{case_text}"',
            "/mesh/check",
            *_thermal_report_lines(config),
            "/exit yes",
        ],
    )


def _write_dry_run_placeholders(output_dir: Path) -> None:
    placeholder = "dry-run placeholder; Fluent was not executed for this artifact.\n"
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        (output_dir / name).write_text(placeholder, encoding="utf-8")


def _runtime_text(output_dir: Path) -> str:
    parts = []
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        path = output_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _first_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        return None
    return float(match.group(1))


def _section_after_marker(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        return ""
    next_prompt = text.find("\n>", start + len(marker))
    if next_prompt < 0:
        return text[start:]
    return text[start:next_prompt]


def _volume_temperature_value(text: str, marker: str, cell_zone: str) -> float | None:
    section = _section_after_marker(text, marker)
    if not section:
        return None
    return _first_float(rf"^\s*{re.escape(cell_zone)}\s+([-+0-9.eE]+)\s*$", section)


def _surface_temperature_value(text: str, surface: str) -> float | None:
    pattern = (
        r"Area-Weighted Average\s+"
        r"Static Temperature\s+\[K\]\s+"
        r"[-\s]+\s*"
        rf"{re.escape(surface)}\s+([-+0-9.eE]+)"
    )
    return _first_float(pattern, text)


def _heat_transfer_rates(text: str) -> dict[str, float]:
    section = _section_after_marker(text, "Total Heat Transfer Rate")
    if not section:
        return {}
    rates: dict[str, float] = {}
    for match in re.finditer(
        rf"^\s*([A-Za-z0-9_.+-]+)\s+({FLOAT_PATTERN})\s*$",
        section,
        flags=re.MULTILINE,
    ):
        rates[match.group(1)] = float(match.group(2))
    return rates


def _collect_thermal_report_metrics(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    reports = config["runtime_smoke"].get("thermal_reports")
    if reports is None:
        return {
            "temperature_runtime_status": "not_requested",
            "heat_rate_runtime_status": "not_requested",
        }
    text = _runtime_text(output_dir)
    cell_zone = reports["cell_zone"]
    surface_temperatures = {
        surface: _surface_temperature_value(text, surface)
        for surface in reports["temperature_surfaces"]
    }
    temperature_min = _volume_temperature_value(text, "Minimum of> temperature", cell_zone)
    temperature_max = _volume_temperature_value(text, "Maximum of> temperature", cell_zone)
    heat_rates = _heat_transfer_rates(text)
    heat_balance_error = None
    heat_net = heat_rates.get("Net")
    heat_denominator = sum(abs(value) for key, value in heat_rates.items() if key != "Net")
    if heat_net is not None and heat_denominator > 0:
        heat_balance_error = abs(heat_net) / heat_denominator
    temperature_complete = (
        temperature_min is not None
        and temperature_max is not None
        and all(value is not None for value in surface_temperatures.values())
    )
    heat_complete = bool(heat_rates) and heat_net is not None and heat_balance_error is not None
    return {
        "temperature_min_k": temperature_min,
        "temperature_max_k": temperature_max,
        "surface_area_weighted_temperature_k": surface_temperatures,
        "temperature_runtime_status": "temperature_reports_extracted"
        if temperature_complete
        else "temperature_report_missing",
        "heat_transfer_rates_w": heat_rates,
        "heat_transfer_net_w": heat_net,
        "heat_transfer_balance_relative_error": heat_balance_error,
        "heat_rate_runtime_status": "heat_transfer_flux_report_extracted"
        if heat_complete
        else "heat_transfer_flux_report_missing",
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
    backend_type = config["backend"]["type"]
    if not dry_run and backend_type == "case_data_manifest":
        raise ValueError("Fluent C07 source readiness manifest is read-only and uses dry_run=True.")
    if backend_type not in {"case_data_manifest", "fluent_case_data_read_smoke"}:
        raise NotImplementedError(f"Fluent C07 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    source_manifest = _build_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "heat_transfer_source_manifest.json",
        "case_data_entries.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    if backend_type == "fluent_case_data_read_smoke":
        archive_path = source_root / config["source_package"]["rel_path"]
        extracted = extract_zip_entries(
            archive_path,
            [config["runtime_smoke"]["case_entry"], config["runtime_smoke"]["data_entry"]],
            resolved_output_dir,
        )
        case_path = next(path for path in extracted if path.name.endswith(".cas.h5"))
        journal_path = _write_runtime_journal(config, resolved_output_dir, case_path, dry_run)
        generated_files.extend([path.name for path in extracted])
        generated_files.extend([journal_path.name, "stdout.txt", "stderr.txt", "transcript.txt"])
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
            return_code = execute_fluent(config, resolved_output_dir, journal_path)
            runtime_metrics = collect_mesh_metrics(resolved_output_dir, return_code)
            runtime_metrics.update(_collect_thermal_report_metrics(config, resolved_output_dir))
        source_manifest["runtime_metrics"] = runtime_metrics
    source_manifest["generated_files"] = generated_files
    (resolved_output_dir / "heat_transfer_source_manifest.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "case_data_entries.json").write_text(json.dumps(source_manifest["case_data_pairs"], indent=2), encoding="utf-8")
    validation = validate_manifest(source_manifest, config)
    metrics = summarize_metrics(source_manifest, validation)
    source_manifest["validation"] = validation
    source_manifest["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "source_manifest": "heat_transfer_source_manifest.json",
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": source_manifest["scope"],
    }
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(source_manifest, config, resolved_output_dir)
    metrics = summarize_metrics(source_manifest, validation)
    source_manifest["validation"] = validation
    source_manifest["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "heat_transfer_source_manifest.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
