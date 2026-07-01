"""Runner for Gmsh C02 physical group boundary contracts."""

from __future__ import annotations

import json
from copy import deepcopy
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_contract_metrics, validate_manifest

SCHEMA_ID = "schemas/gmsh_C02_boundary_physical_group_contract.schema.json"


def _physical_group_map(config: dict[str, Any]) -> dict[str, Any]:
    groups_by_name = {}
    groups_by_role: dict[str, list[str]] = defaultdict(list)
    for group in config["physical_groups"]:
        groups_by_name[group["name"]] = {
            "name": group["name"],
            "dimension": group["dimension"],
            "role": group["role"],
            "required": group["required"],
            "downstream_aliases": group["downstream_aliases"],
        }
        groups_by_role[group["role"]].append(group["name"])
    return {
        "groups_by_name": groups_by_name,
        "groups_by_role": {role: sorted(names) for role, names in groups_by_role.items()},
    }


def _boundary_contract(config: dict[str, Any]) -> dict[str, Any]:
    role_to_boundary_type = config["downstream_boundary_map"]["role_to_boundary_type"]
    solver_boundaries = []
    for group in config["physical_groups"]:
        solver_boundaries.append(
            {
                "group_name": group["name"],
                "dimension": group["dimension"],
                "role": group["role"],
                "required": group["required"],
                "downstream_aliases": group["downstream_aliases"],
                "solver_boundary_type": role_to_boundary_type.get(group["role"]),
            }
        )
    return {
        "target_solver": config["downstream_boundary_map"]["target_solver"],
        "required_roles": config["downstream_boundary_map"]["required_roles"],
        "solver_boundaries": solver_boundaries,
        "role_to_boundary_type": role_to_boundary_type,
    }


def _write_contract_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    group_map = _physical_group_map(config)
    contract = _boundary_contract(config)
    (output_dir / "physical_group_map.json").write_text(json.dumps(group_map, indent=2), encoding="utf-8")
    (output_dir / "boundary_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    generated_files = ["physical_group_map.json", "boundary_contract.json"]
    replay = config.get("downstream_import_replay") or {}
    if replay.get("enabled"):
        summary_path = repo_relative_path(replay["source_summary_path"])
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        (output_dir / "downstream_import_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        generated_files.append("downstream_import_summary.json")
    return generated_files


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "geometry": config["geometry"],
        "physical_groups": config["physical_groups"],
        "downstream_boundary_map": config["downstream_boundary_map"],
        **({"downstream_import_replay": config["downstream_import_replay"]} if config.get("downstream_import_replay") else {}),
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build physical_group_map.json",
            "static-contract:build boundary_contract.json",
        ],
        "scope": "static physical group boundary contract; no mesh generation or solver execution",
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
        raise ValueError("Gmsh C02 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Gmsh C02 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    validation_config = deepcopy(config)
    replay = validation_config.get("downstream_import_replay") or {}
    if replay.get("enabled"):
        summary_path = repo_relative_path(replay["source_summary_path"])
        replay["_summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    generated_files = _write_contract_artifacts(resolved_output_dir, validation_config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(validation_config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, validation_config)
    metrics = summarize_contract_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, validation_config, resolved_output_dir)
    metrics = summarize_contract_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
