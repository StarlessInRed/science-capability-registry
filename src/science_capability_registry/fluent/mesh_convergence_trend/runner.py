"""Runner for Fluent C03 mesh convergence trend contracts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from science_capability_registry.fluent.verification_reference_validation.config import load_case_config as load_c02_config
from science_capability_registry.fluent.verification_reference_validation.config import validate_case_config as validate_c02_config
from science_capability_registry.fluent.verification_reference_validation.runner import run as run_c02

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_metrics, summarize_runtime_metrics, validate_manifest, validate_runtime_manifest

SCHEMA_ID = "schemas/fluent_C03_mesh_convergence_trend.schema.json"


def _trend_contract(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return {
        "schema_id": SCHEMA_ID,
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "validated_config": True,
        "output_dir": str(output_dir),
        "backend": config["backend"],
        "source_basis": config["source_basis"],
        "mesh_levels": config["mesh_levels"],
        "monitored_quantities": config["monitored_quantities"],
        "failure_classification": config["failure_classification"],
        "validation_targets": config["validation"],
        "no_claims": config["validation"]["no_claims"],
        "scope": "Fluent C03 mesh convergence static trend contract; no solver execution",
    }


def _write_refinement_matrix(path: Path, mesh_levels: list[dict[str, Any]]) -> None:
    columns = [
        "level_id",
        "refinement_index",
        "nominal_cell_count",
        "relative_cell_size",
        "input_role",
        "runtime_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for level in mesh_levels:
            writer.writerow({column: level[column] for column in columns})


def _write_runtime_refinement_matrix(path: Path, runtime_levels: list[dict[str, Any]]) -> None:
    columns = [
        "level_id",
        "refinement_index",
        "nominal_cell_count",
        "axial_cells",
        "radial_cells",
        "validation_passed",
        "runtime_pressure_drop_pa",
        "pressure_drop_relative_error",
        "final_continuity_residual",
        "iteration_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for level in runtime_levels:
            writer.writerow({column: level.get(column) for column in columns})


def _runtime_contract(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    contract = _trend_contract(config, output_dir)
    contract["runtime_basis"] = config["runtime_basis"]
    contract["scope"] = (
        "Fluent C03 runtime mesh-refinement smoke using the C02 pressure-solve runner; "
        "uniform-inlet analytical homology remains unclaimed"
    )
    return contract


def _level_config(base_config: dict[str, Any], level: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    output_prefix = config["runtime_basis"]["level_output_prefix"].rstrip("/")
    case_id = f"{config['case_id']}_{level['level_id']}"
    updated = dict(base_config)
    updated["case_id"] = case_id
    updated["mesh_generation"] = {
        **base_config["mesh_generation"],
        "axial_cells": level["axial_cells"],
        "radial_cells": level["radial_cells"],
    }
    updated["solver_setup"] = {
        **base_config["solver_setup"],
        "max_iterations": config["runtime_basis"]["max_iterations"],
    }
    updated["outputs"] = {
        **base_config["outputs"],
        "output_dir": f"{output_prefix}_{level['level_id']}",
    }
    return validate_c02_config(updated)


def _run_runtime(config: dict[str, Any], output_dir: Path, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        raise ValueError("Fluent C03 c02_pressure_drop_refinement_runtime_smoke requires dry_run=False.")

    output_dir.mkdir(parents=True, exist_ok=True)
    base_config = load_c02_config(config["runtime_basis"]["template_config"])
    runtime_levels = []
    for level in config["mesh_levels"]:
        level_config = _level_config(base_config, level, config)
        result = run_c02(config=level_config, dry_run=False)
        metrics = result["metrics"]
        final_residuals = metrics.get("final_residuals", {})
        runtime_levels.append(
            {
                **level,
                "case_id": level_config["case_id"],
                "output_dir": level_config["outputs"]["output_dir"],
                "validation_passed": bool(result["validation"]["passed"]),
                "runtime_pressure_drop_pa": metrics.get("runtime_pressure_drop_pa"),
                "pressure_drop_relative_error": metrics.get("pressure_drop_relative_error"),
                "final_continuity_residual": final_residuals.get("continuity"),
                "iteration_count": metrics.get("iteration_count"),
                "pressure_drop_runtime_status": metrics.get("pressure_drop_runtime_status"),
            }
        )

    generated_files = [
        "trend_contract.json",
        "refinement_matrix.csv",
        "runtime_levels.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    contract = _runtime_contract(config, output_dir)
    contract["generated_files"] = generated_files
    contract["runtime_levels"] = runtime_levels
    (output_dir / "trend_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (output_dir / "runtime_levels.json").write_text(json.dumps(runtime_levels, indent=2), encoding="utf-8")
    _write_runtime_refinement_matrix(output_dir / "refinement_matrix.csv", runtime_levels)

    validation = validate_runtime_manifest(contract, config)
    metrics = summarize_runtime_metrics(contract, validation)
    contract["validation"] = validation
    contract["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(output_dir),
        "runtime_basis": config["runtime_basis"],
        "runtime_levels": runtime_levels,
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": contract["scope"],
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_dir / "validation_report.md", config, metrics, validation)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_runtime_manifest(contract, config, output_dir)
    metrics = summarize_runtime_metrics(contract, validation)
    contract["validation"] = validation
    contract["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (output_dir / "trend_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_dir / "validation_report.md", config, metrics, validation)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


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
    if backend_type == "c02_pressure_drop_refinement_runtime_smoke":
        resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
        return _run_runtime(config, resolved_output_dir, dry_run=dry_run)
    if not dry_run:
        raise ValueError("Fluent C03 mesh convergence contract is static and uses dry_run=True.")
    if backend_type != "mesh_trend_static":
        raise NotImplementedError(f"Fluent C03 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    contract = _trend_contract(config, resolved_output_dir)
    generated_files = [
        "trend_contract.json",
        "refinement_matrix.csv",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    contract["generated_files"] = generated_files
    (resolved_output_dir / "trend_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    _write_refinement_matrix(resolved_output_dir / "refinement_matrix.csv", config["mesh_levels"])
    validation = validate_manifest(contract, config)
    metrics = summarize_metrics(contract, validation)
    contract["validation"] = validation
    contract["metrics"] = metrics
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(resolved_output_dir),
        "trend_contract": "trend_contract.json",
        "source_basis": config["source_basis"],
        "mesh_levels": config["mesh_levels"],
        "monitored_quantities": config["monitored_quantities"],
        "failure_classification": config["failure_classification"],
        "generated_files": generated_files,
        "metrics": metrics,
        "validation": validation,
        "scope": contract["scope"],
    }
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(contract, config, resolved_output_dir)
    metrics = summarize_metrics(contract, validation)
    contract["validation"] = validation
    contract["metrics"] = metrics
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "trend_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
