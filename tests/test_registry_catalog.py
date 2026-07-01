from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from science_capability_registry.registry.catalog import (
    catalog_entries_by_id,
    evidence_entries_by_id,
    load_catalog,
    load_evidence_index,
    repo_path,
    resolve_capability,
)
from science_capability_registry.registry.dispatcher import RUNNERS, build_dispatch_plan, run_capability


FORBIDDEN_CATALOG_FIELDS = {
    "physics",
    "inputs",
    "outputs",
    "benchmark",
    "validation_criteria",
    "reference_observations",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _validate_json(data: dict[str, Any], schema_path: Path) -> None:
    schema = _read_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    assert not errors, "\n".join(f"{'.'.join(str(part) for part in error.path)}: {error.message}" for error in errors)


def _repo_relative(path_value: str) -> bool:
    path = Path(path_value)
    return not path.is_absolute() and ":" not in path_value and "\\" not in path_value


def test_capability_catalog_validates_and_covers_package_backed_assets() -> None:
    catalog = load_catalog()
    _validate_json(catalog, Path("schemas/capability_registry.schema.json"))

    assert len(catalog["capabilities"]) == 20
    assert len(catalog_entries_by_id(catalog)) == 20
    for entry in catalog["capabilities"]:
        assert repo_path(entry["asset_path"]).exists()

    catalog_asset_paths = {entry["asset_path"] for entry in catalog["capabilities"]}
    assert "software/openfoam/assets/C05_transient_cylinder_vortex_shedding.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C01_parametric_geometry_mesh_generation.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C02_boundary_physical_group_contract.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C03_mesh_refinement_quality_trend.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C04_cad_import_geometry_healing.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C05_boundary_layer_size_field_meshing.yaml" in catalog_asset_paths
    assert "software/gmsh/assets/C06_multi_solver_mesh_export_contract.yaml" in catalog_asset_paths


def test_capability_catalog_entries_match_asset_cards_and_configs() -> None:
    catalog = load_catalog()
    for entry in catalog["capabilities"]:
        assert not (FORBIDDEN_CATALOG_FIELDS & set(entry))
        for key in ["asset_path", "run_schema_path", "default_config_path"]:
            assert _repo_relative(entry[key]), f"{entry['capability_id']} has non-repo-relative {key}: {entry[key]}"
            assert repo_path(entry[key]).exists(), f"{entry['capability_id']} missing {key}: {entry[key]}"
        for key in ["runtime_profile_path", "benchmark_manifest_path"]:
            if key in entry:
                assert _repo_relative(entry[key]), f"{entry['capability_id']} has non-repo-relative {key}: {entry[key]}"
                assert repo_path(entry[key]).exists(), f"{entry['capability_id']} missing {key}: {entry[key]}"
        assert entry["primary_evidence_id"] in entry["evidence_ids"]
        assert entry["result_contract"]["required_files"] == [
            "manifest.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
        ]
        assert entry["result_contract"]["runtime_evidence_index"] == "reports/evidence_index.yaml"

        asset = _read_yaml(repo_path(entry["asset_path"]))
        assert entry["asset_id"] == asset["asset_id"]
        assert entry["software"] == asset["software"]
        assert entry["domain"] == asset["domain"]
        assert entry["card_status"] == asset["card_status"]
        assert entry["benchmark_status"] == asset["benchmark_status"]
        assert entry["run_schema_path"] == asset["integration_targets"]["input_schema"]
        assert entry["package_entrypoint"] == asset["integration_targets"]["package_entrypoint"]
        assert entry["capability_id"] == asset["integration_targets"]["workflow_stage"]

        config = _read_yaml(repo_path(entry["default_config_path"]))
        assert config["capability_id"] == entry["capability_id"]
        _validate_json(config, repo_path(entry["run_schema_path"]))


def test_evidence_index_resolves_catalog_evidence_ids() -> None:
    catalog = load_catalog()
    evidence_index = load_evidence_index()
    evidence = evidence_entries_by_id(evidence_index)

    assert evidence_index["index_id"] == "science_capability_registry.evidence_index"
    for entry in catalog["capabilities"]:
        assert entry["primary_evidence_id"] in evidence
        for evidence_id in entry["evidence_ids"]:
            assert evidence_id in evidence
            evidence_entry = evidence[evidence_id]
            assert evidence_entry["capability_id"] == entry["capability_id"]
            assert evidence_entry["asset_path"] == entry["asset_path"]
            assert repo_path(evidence_entry["primary_evidence_path"]).exists()
            for path in evidence_entry.get("supporting_paths", []):
                assert repo_path(path).exists(), f"{evidence_id} missing supporting path: {path}"

        if entry["benchmark_status"] == "benchmark_validated":
            assert any(evidence[evidence_id]["status"] == "passed" for evidence_id in entry["evidence_ids"])


def test_dispatcher_runner_keys_match_catalog_and_can_dry_run_cantera_c01(tmp_path: Path) -> None:
    catalog_ids = set(catalog_entries_by_id(load_catalog()))
    assert set(RUNNERS) == catalog_ids

    plan = build_dispatch_plan()
    assert plan["validated_config"] is True
    assert {entry["capability_id"] for entry in plan["entries"]} == catalog_ids
    openfoam_c08 = next(
        entry
        for entry in plan["entries"]
        if entry["capability_id"] == "cfd.openfoam.compressible_shock_capturing_forward_step"
    )
    assert openfoam_c08["dispatch_status"] == "replay_ready"
    assert openfoam_c08["current_gate"] == "smoke"
    assert openfoam_c08["primary_evidence_id"] == "openfoam_C08_cfl_reduced_runtime_smoke_2026-07-01"
    assert openfoam_c08["runtime_profile_path"] == "configs/openfoam/runtime_profiles/openfoam_com_v2112.yaml"

    result = run_capability(
        "combustion.cantera.constant_pressure_ignition",
        output_dir=tmp_path / "c01_dry_run",
        dry_run=True,
    )
    assert result["validated_config"] is True
    assert result["capability_id"] == "combustion.cantera.constant_pressure_ignition"


def test_resolve_capability_rejects_unknown_id() -> None:
    try:
        resolve_capability("missing.capability")
    except ValueError as exc:
        assert "Unknown capability_id" in str(exc)
    else:
        raise AssertionError("resolve_capability should reject unknown ids")
