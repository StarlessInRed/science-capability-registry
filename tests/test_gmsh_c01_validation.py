from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.gmsh.parametric_geometry_mesh_generation.validation import (
    validate_manifest,
    validate_mesh_summary,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml").read_text(encoding="utf-8"))


def _openfoam_import_config() -> dict:
    return yaml.safe_load(
        Path("configs/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112.yaml").read_text(encoding="utf-8")
    )


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


def test_gmsh_c01_validation_accepts_openfoam_import_summary(tmp_path: Path) -> None:
    config = _openfoam_import_config()
    for rel_path in config["outputs"]["expected_outputs"]:
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("1\n(\n0\n)\n", encoding="utf-8")

    expected_files = {
        rel_path: {"path": str(tmp_path / rel_path), "exists": True, "size_bytes": 8}
        for rel_path in config["downstream_import"]["expected_outputs"]
    }
    summary = {
        "node_count": 10,
        "element_count": 12,
        "coordinates_finite": True,
        "physical_groups": {"inlet": {}, "outlet": {}, "wall": {}, "frontAndBack": {}, "fluid_domain": {}},
        "quality": {"min_quality_proxy": 0.5},
        "downstream_import": {
            "enabled": True,
            "status": "passed",
            "polyMesh": {
                "files": expected_files,
                "counts": {"points": 10, "faces": 20, "owner": 20, "neighbour": 8},
                "boundary_names": ["inlet", "outlet", "wall", "frontAndBack"],
                "structural_checks": {
                    "has_points": True,
                    "has_faces": True,
                    "owner_matches_faces": True,
                    "neighbour_not_larger_than_faces": True,
                },
            },
        },
    }

    result = validate_mesh_summary(summary, config, tmp_path)

    assert result["passed"] is True
