"""Runner for Gmsh C06 multi-solver export contracts."""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import summarize_export_metrics, validate_manifest

SCHEMA_ID = "schemas/gmsh_C06_multi_solver_mesh_export_contract.schema.json"


def _resolve_observation(config: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    path = repo_relative_path(observation["source_summary_path"])
    if observation["summary_kind"] == "openfoam_downstream_import":
        data = json.loads(path.read_text(encoding="utf-8"))
        poly_mesh = data.get("polyMesh", {})
        counts = poly_mesh.get("counts", {})
        return {
            "target_id": observation["target_id"],
            "summary_kind": observation["summary_kind"],
            "source_summary_path": observation["source_summary_path"],
            "status": data.get("status"),
            "boundary_names": poly_mesh.get("boundary_names", []),
            "element_count": counts.get("neighbour") or counts.get("faces"),
            "structural_checks": poly_mesh.get("structural_checks", {}),
        }
    if observation["summary_kind"] == "gmsh_mesh_summary_fixture":
        data = json.loads(path.read_text(encoding="utf-8"))
        level_summaries = data.get("level_summaries", [])
        selected = level_summaries[-1] if level_summaries else {}
        physical_groups = selected.get("physical_groups", {})
        return {
            "target_id": observation["target_id"],
            "summary_kind": observation["summary_kind"],
            "source_summary_path": observation["source_summary_path"],
            "status": observation["expected_status"] if selected else "failed",
            "boundary_names": sorted(name for name in physical_groups if name != "fluid_domain"),
            "element_count": selected.get("element_count"),
            "structural_checks": {
                "has_nodes": int(selected.get("node_count", 0)) > 0,
                "has_elements": int(selected.get("element_count", 0)) > 0,
                "coordinates_finite": selected.get("coordinates_finite") is True,
            },
        }
    if observation["summary_kind"] == "meshio_fem_import":
        try:
            import meshio
        except ModuleNotFoundError as exc:
            raise RuntimeError("meshio is required for C06 meshio_fem_import observations.") from exc
        mesh = meshio.read(path)
        cell_counts = {cell_block.type: int(len(cell_block.data)) for cell_block in mesh.cells}
        boundary_names = sorted(
            name
            for name in mesh.cell_sets_dict
            if name != "gmsh:bounding_entities"
        )
        element_count = sum(cell_counts.values())
        return {
            "target_id": observation["target_id"],
            "summary_kind": observation["summary_kind"],
            "source_summary_path": observation["source_summary_path"],
            "status": observation["expected_status"] if mesh.points.size and element_count else "failed",
            "boundary_names": boundary_names,
            "element_count": element_count,
            "cell_counts": cell_counts,
            "structural_checks": {
                "has_points": int(len(mesh.points)) > 0,
                "has_cells": element_count > 0,
                "has_field_data": bool(mesh.field_data),
                "has_named_cell_sets": bool(boundary_names),
            },
        }
    raise ValueError(f"Unsupported import observation kind: {observation['summary_kind']!r}")


def _resolve_observations(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [_resolve_observation(config, observation) for observation in config.get("import_observations", [])]


def _write_export_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    export_manifest = {
        "source_mesh": config["source_mesh"],
        "unit_policy": config["unit_policy"],
        "orientation_policy": config["orientation_policy"],
        "export_targets": config["export_targets"],
        "import_observations": config.get("_resolved_import_observations", []),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(export_manifest, indent=2), encoding="utf-8")
    with (output_dir / "format_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_id",
                "solver_family",
                "target_solver",
                "export_format",
                "contract_status",
                "expected_boundary_names",
                "expected_element_count_min",
                "max_element_count_delta_fraction",
            ],
        )
        writer.writeheader()
        for target in config["export_targets"]:
            writer.writerow(
                {
                    **target,
                    "expected_boundary_names": "|".join(target["expected_boundary_names"]),
                }
            )
    observations = config.get("_resolved_import_observations", [])
    import_summary = {
        "status": "passed" if observations and all(item.get("status") == "passed" for item in observations) else "static_contract_only",
        "successful_import_count": sum(1 for item in observations if item.get("status") == "passed"),
        "targets": config["export_targets"],
        "observations": observations,
        "scope": "OpenFOAM replay plus lightweight downstream importer observations; no downstream physics solve executed by C06",
    }
    (output_dir / "solver_import_summary.json").write_text(json.dumps(import_summary, indent=2), encoding="utf-8")
    return ["export_manifest.json", "format_matrix.csv", "solver_import_summary.json"]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "output_dir": str(output_dir),
        "gmsh": config["gmsh"],
        "backend": config["backend"],
        "source_mesh": config["source_mesh"],
        "unit_policy": config["unit_policy"],
        "orientation_policy": config["orientation_policy"],
        "export_targets": config["export_targets"],
        **({"import_observations": config["import_observations"]} if config.get("import_observations") else {}),
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "static-contract:build export_manifest.json",
            "static-contract:build format_matrix.csv",
            "static-contract:build solver_import_summary.json",
            *(
                f"meshio:read {item['source_summary_path']}"
                for item in config.get("import_observations", [])
                if item["summary_kind"] == "meshio_fem_import"
            ),
        ],
        "scope": "multi-solver export contract with replay/lightweight importer observations",
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
        raise ValueError("Gmsh C06 currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"Gmsh C06 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    validation_config = deepcopy(config)
    validation_config["_resolved_import_observations"] = _resolve_observations(validation_config)
    generated_files = _write_export_artifacts(resolved_output_dir, validation_config)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(validation_config, resolved_output_dir, generated_files)
    validation = validate_manifest(manifest, validation_config)
    metrics = summarize_export_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics

    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_manifest(manifest, validation_config, resolved_output_dir)
    metrics = summarize_export_metrics(validation_config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", validation_config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
