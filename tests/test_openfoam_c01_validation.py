from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.runner import (
    run,
)
from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.validation import (
    validate_manifest,
)


def _baseline_config() -> dict:
    with open(
        "configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def test_openfoam_c01_validation_accepts_complete_dry_run_manifest() -> None:
    manifest = run(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/test_validation"),
        dry_run=True,
    )
    output_dir = Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/test_validation")
    result = validate_manifest(manifest, _baseline_config(), output_dir)
    assert result["passed"] is True


def test_openfoam_c01_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline.yaml",
        "schema_id": "schemas/openfoam_C01_lid_driven_cavity_incompressible_laminar.schema.json",
        "backend": {"type": "dry_run_only"},
        "generated_files": ["case/0/U"],
        "mesh_commands": ["blockMesh"],
        "solver_commands": ["icoFoam"],
        "expected_outputs": [],
        "validation_targets": {},
    }
    result = validate_manifest(manifest, config)
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/p" in failed
