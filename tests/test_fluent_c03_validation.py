from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.mesh_convergence_trend.config import validate_case_config
from science_capability_registry.fluent.mesh_convergence_trend.runner import run
from science_capability_registry.fluent.mesh_convergence_trend.validation import validate_manifest


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

