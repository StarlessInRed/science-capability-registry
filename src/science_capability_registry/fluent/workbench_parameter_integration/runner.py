"""Runner for Fluent C08 Workbench parameter static preflight."""

from __future__ import annotations

import ast
import csv
import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from science_capability_registry.fluent.official_replay_manifest.zip_catalog import inspect_zip_archive, summarize_entries

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_metrics, validate_manifest

SCHEMA_ID = "schemas/fluent_C08_workbench_parameter_integration.schema.json"


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


def _nested_entry_kind(entry_path: str) -> str:
    name = Path(entry_path).name.lower()
    if name.endswith(".wbpj"):
        return "workbench_project_file"
    if name.endswith(".wbdp"):
        return "design_point_file"
    if name.endswith(".wbjn"):
        return "workbench_journal"
    if name == "designpointlog.csv":
        return "design_point_log"
    if name.endswith(".agdb"):
        return "geometry_database"
    if name.endswith(".mshdb"):
        return "mesh_database"
    if name == "act.dat":
        return "auxiliary_state"
    if name == ".project_cache":
        return "project_cache"
    return "other"


def _nested_entries(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    entries = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        entries.append(
            {
                "entry_path": info.filename,
                "entry_kind": _nested_entry_kind(info.filename),
                "size": int(info.file_size),
                "compressed_size": int(info.compress_size),
                "crc32": int(info.CRC),
            }
        )
    return entries


def _summarize_nested_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for entry in entries:
        kind = entry["entry_kind"]
        counts[kind] = counts.get(kind, 0) + 1
    return {"entry_count": len(entries), "entry_kind_counts": counts}


def _text_by_kind(archive: zipfile.ZipFile, entries: list[dict[str, Any]], kind: str) -> str:
    matches = [entry["entry_path"] for entry in entries if entry["entry_kind"] == kind]
    if not matches:
        return ""
    return archive.read(matches[0]).decode("utf-8-sig", errors="replace")


def _child_text(root: ElementTree.Element, tag: str) -> str:
    node = root.find(f".//{tag}")
    return (node.text or "").strip() if node is not None else ""


def _parse_project_metadata(wbpj_text: str) -> dict[str, str]:
    if not wbpj_text:
        return {"framework_build_version": "", "external_version_string": "", "last_saved_utc": "", "project_version": ""}
    root = ElementTree.fromstring(wbpj_text)
    project = root.find(".//Project")
    return {
        "framework_build_version": _child_text(root, "framework-build-version"),
        "external_version_string": _child_text(root, "external-version-string"),
        "last_saved_utc": _child_text(root, "last-saved-utc"),
        "project_version": project.attrib.get("Version", "") if project is not None else "",
    }


def _parse_current_parameters(wbpj_text: str) -> list[dict[str, str]]:
    if not wbpj_text:
        return []
    root = ElementTree.fromstring(wbpj_text)
    parameters = []
    for node in root.findall(".//Object"):
        name = node.attrib.get("Name", "")
        if not name.startswith("/Parameters/Parameter:"):
            continue
        object_name = _child_text(node, "object-name")
        member_node = node.find("member-data")
        member_text = member_node.text if member_node is not None and member_node.text else "{}"
        try:
            member_data = ast.literal_eval(member_text)
        except (SyntaxError, ValueError):
            member_data = {}
        value = member_data.get("Value", {})
        value_spec = member_data.get("ValueSpec", {})
        parameters.append(
            {
                "parameter_name": object_name,
                "display_text": str(member_data.get("DisplayText", "")),
                "expression": str(member_data.get("Expression", "")),
                "usage": str(member_data.get("Usage", "")),
                "value": str(value.get("value", "")) if isinstance(value, dict) else "",
                "quantity_name": str(value_spec.get("QuantityName", "")) if isinstance(value_spec, dict) else "",
            }
        )
    return sorted(parameters, key=lambda item: item["parameter_name"])


def _parse_design_point_log(log_text: str) -> dict[str, Any]:
    rows = []
    headers = []
    if log_text:
        for row in csv.reader(io.StringIO(log_text.replace("\ufeff", ""))):
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            normalized = [cell.strip() for cell in row]
            if normalized[0] == "Name":
                headers = normalized
            else:
                rows.append(normalized)
    return {"headers": headers, "data_row_count": len(rows), "sample_rows": rows[:5]}


def _write_parameter_table(path: Path, parameters: list[dict[str, str]]) -> None:
    columns = ["parameter_name", "display_text", "expression", "usage", "value", "quantity_name"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for parameter in parameters:
            writer.writerow(parameter)


def _env_probe(env_name: str) -> dict[str, Any]:
    value = os.environ.get(env_name, "")
    exists = Path(value).exists() if value else False
    return {"env_name": env_name, "configured": bool(value), "path_exists": exists}


def _runwb2_preflight(config: dict[str, Any]) -> dict[str, Any]:
    envs = config["environment_preflight"]
    return {
        "static_gate_requires_runwb2": envs["static_gate_requires_runwb2"],
        "runwb2_executable": _env_probe(envs["runwb2_executable_env"]),
        "fluent_executable": _env_probe(envs["fluent_executable_env"]),
        "ansys_root": _env_probe(envs["ansys_root_env"]),
    }


def _build_manifest(config: dict[str, Any], output_dir: Path, source_root: Path) -> dict[str, Any]:
    outer_path = source_root / config["source_package"]["rel_path"]
    outer_entries = []
    nested_entries: list[dict[str, Any]] = []
    current_parameters: list[dict[str, str]] = []
    project_metadata = {"framework_build_version": "", "external_version_string": "", "last_saved_utc": "", "project_version": ""}
    design_point_log = {"headers": [], "data_row_count": 0, "sample_rows": []}
    outer_status = "readable"
    nested_status = "readable"
    outer_error = ""
    nested_error = ""
    try:
        outer_entries = inspect_zip_archive(outer_path)
        with zipfile.ZipFile(outer_path) as outer:
            nested_bytes = outer.read(config["source_package"]["nested_wbpz_entry"])
        with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
            nested_entries = _nested_entries(nested)
            wbpj_text = _text_by_kind(nested, nested_entries, "workbench_project_file")
            project_metadata = _parse_project_metadata(wbpj_text)
            current_parameters = _parse_current_parameters(wbpj_text)
            design_point_log = _parse_design_point_log(_text_by_kind(nested, nested_entries, "design_point_log"))
    except Exception as exc:
        if outer_entries:
            nested_status = "unreadable"
            nested_error = str(exc)
        else:
            outer_status = "unreadable"
            outer_error = str(exc)
            nested_status = "unreadable"
            nested_error = str(exc)
    outer_summary = summarize_entries(outer_entries)
    nested_summary = _summarize_nested_entries(nested_entries)
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
        "workbench_scope": config["workbench_scope"],
        "outer_archive": {
            "archive_status": outer_status,
            "error_message": outer_error,
            "entry_count": outer_summary["entry_count"],
            "entry_kind_counts": outer_summary["entry_kind_counts"],
        },
        "outer_entries": outer_entries,
        "nested_archive": {
            "archive_status": nested_status,
            "error_message": nested_error,
            "entry_count": nested_summary["entry_count"],
            "entry_kind_counts": nested_summary["entry_kind_counts"],
        },
        "nested_entries": nested_entries,
        "workbench_project": project_metadata,
        "current_parameters": current_parameters,
        "design_point_log": design_point_log,
        "runwb2_preflight": _runwb2_preflight(config),
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "scope": "read-only Fluent C08 Workbench WBPZ static preflight; no Workbench execution",
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
        raise ValueError("Fluent C08 Workbench preflight is read-only and uses dry_run=True.")
    if config["backend"]["type"] != "workbench_project_manifest":
        raise NotImplementedError(f"Fluent C08 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    source_root = _source_root(config, require_exists=True)
    workbench_manifest = _build_manifest(config, resolved_output_dir, source_root)
    generated_files = [
        "workbench_project_manifest.json",
        "workbench_entries.json",
        "parameter_table.csv",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    workbench_manifest["generated_files"] = generated_files
    (resolved_output_dir / "workbench_project_manifest.json").write_text(json.dumps(workbench_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "workbench_entries.json").write_text(json.dumps(workbench_manifest["nested_entries"], indent=2), encoding="utf-8")
    _write_parameter_table(resolved_output_dir / "parameter_table.csv", workbench_manifest["current_parameters"])
    validation = validate_manifest(workbench_manifest, config)
    metrics = summarize_metrics(workbench_manifest, validation)
    workbench_manifest["validation"] = validation
    workbench_manifest["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "workbench_project_manifest": "workbench_project_manifest.json",
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": workbench_manifest["scope"],
    }
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(workbench_manifest, config, resolved_output_dir)
    metrics = summarize_metrics(workbench_manifest, validation)
    workbench_manifest["validation"] = validation
    workbench_manifest["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "workbench_project_manifest.json").write_text(json.dumps(workbench_manifest, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
