from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.gmsh.parametric_geometry_mesh_generation.validation import (
    validate_manifest,
    validate_mesh_summary,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml").read_text(encoding="utf-8"))


def test_gmsh_c01_validation_rejects_missing_physical_group() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline.yaml",
        "schema_id": "schemas/gmsh_C01_parametric_geometry_mesh_generation.schema.json",
        "backend": {"type": "dry_run_only"},
        "gmsh": config["gmsh"],
        "geometry": config["geometry"],
        "physical_groups": [item for item in config["physical_groups"] if item["name"] != "outlet"],
        "mesh": config["mesh"],
        "generated_files": ["case.geo"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
    }

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "physical_groups.required" in failed


def test_gmsh_c01_validation_rejects_bad_mesh_summary() -> None:
    config = _baseline_config()
    summary = {
        "node_count": 0,
        "element_count": 0,
        "coordinates_finite": False,
        "physical_groups": {"inlet": {}, "wall": {}, "fluid_domain": {}},
        "quality": {"min_quality_proxy": 0.0},
    }

    result = validate_mesh_summary(summary, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "mesh.node_count" in failed
    assert "mesh.element_count" in failed
    assert "physical_groups.required" in failed
