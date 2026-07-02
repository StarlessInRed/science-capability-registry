from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.mesh_convergence_trend.config import validate_case_config
from science_capability_registry.fluent.mesh_convergence_trend.runner import run
from science_capability_registry.fluent.mesh_convergence_trend.validation import validate_manifest, validate_runtime_manifest


def _load_config() -> dict:
    data = yaml.safe_load(
        Path("configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(data)


def test_fluent_c03_validation_accepts_static_trend_contract(tmp_path: Path) -> None:
    config = _load_config()
    manifest = run(config=deepcopy(config), output_dir=tmp_path, dry_run=True)

    validation = validate_manifest(manifest, config, tmp_path)

    assert validation["passed"] is True
    assert any(item["name"] == "trend.min_mesh_levels" and item["passed"] for item in validation["checks"])
    assert any(
        item["name"] == "trend.cell_counts_strictly_increasing" and item["passed"]
        for item in validation["checks"]
    )


def test_fluent_c03_validation_rejects_nonmonotonic_cell_counts(tmp_path: Path) -> None:
    config = _load_config()
    manifest = run(config=deepcopy(config), output_dir=tmp_path, dry_run=True)
    manifest["mesh_levels"][2]["nominal_cell_count"] = 1000

    validation = validate_manifest(manifest, config, tmp_path)

    assert validation["passed"] is False
    assert any(
        item["name"] == "trend.cell_counts_strictly_increasing" and not item["passed"]
        for item in validation["checks"]
    )


def test_fluent_c03_validation_accepts_runtime_pressure_trend() -> None:
    config = validate_case_config(
        yaml.safe_load(
            Path("configs/fluent/mesh_convergence_trend/c02_pressure_drop_refinement_runtime_smoke.yaml").read_text(
                encoding="utf-8"
            )
        )
    )
    manifest = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_basis": config["source_basis"],
        "mesh_levels": config["mesh_levels"],
        "monitored_quantities": config["monitored_quantities"],
        "failure_classification": config["failure_classification"],
        "generated_files": config["outputs"]["expected_outputs"],
        "runtime_levels": [
            {
                **level,
                "validation_passed": True,
                "runtime_pressure_drop_pa": value,
                "pressure_drop_relative_error": 0.24,
            }
            for level, value in zip(config["mesh_levels"], [12.44, 12.70, 12.78])
        ],
    }

    validation = validate_runtime_manifest(manifest, config)

    assert validation["passed"] is True
    assert any(
        item["name"] == "runtime.adjacent_pressure_drop_change_bound" and item["passed"]
        for item in validation["checks"]
    )
