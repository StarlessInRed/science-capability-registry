from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.dam_break_vof_free_surface.runtime import (
    validate_runtime_metrics,
)
from science_capability_registry.openfoam.dam_break_vof_free_surface.validation import (
    validate_manifest,
)


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_openfoam_c06_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline.yaml",
        "schema_id": "schemas/openfoam_C06_dam_break_vof_free_surface.schema.json",
        "backend": {"type": "dry_run_only"},
        "generated_files": ["case/0/U"],
        "mesh_commands": ["blockMesh"],
        "solver_commands": ["interFoam"],
        "expected_outputs": [],
        "validation_targets": {},
    }

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/alpha.water" in failed


def test_openfoam_c06_runtime_validation_rejects_unbounded_alpha() -> None:
    config = _baseline_config()
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "setFields", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "interFoam", "returncode": 0},
            ]
        },
        "mesh": {"mesh_ok": True},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_s"],
            "max_courant_number": 0.5,
            "max_alpha_courant_number": 0.5,
        },
        "postprocess": {
            "alpha_finite": True,
            "alpha_bounds": {"alpha_min": 0.0, "alpha_max": 1.2},
            "volume": {"relative_error": 0.0},
            "front": {"front_x_m": 0.1},
        },
    }

    result = validate_runtime_metrics(metrics, config, Path("_results/openfoam/c06_missing"))

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "alpha.upper_bound" in failed
