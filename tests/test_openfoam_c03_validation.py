from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow.validation import (
    validate_manifest,
)
from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow.runtime import (
    validate_runtime_metrics,
)


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/backward_facing_step_rans_internal_flow/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_openfoam_c03_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline.yaml",
        "schema_id": "schemas/openfoam_C03_backward_facing_step_rans_internal_flow.schema.json",
        "backend": {"type": "dry_run_only"},
        "generated_files": ["case/0/U"],
        "mesh_commands": ["blockMesh"],
        "solver_commands": ["simpleFoam"],
        "expected_outputs": [],
        "validation_targets": {},
    }

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/p" in failed


def test_openfoam_c03_runtime_validation_rejects_bad_residual() -> None:
    config = _baseline_config()
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "simpleFoam", "returncode": 0},
            ]
        },
        "mesh": {"mesh_ok": True},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_iterations"],
            "last_residuals": {"Ux": {"final": 1.0}},
            "last_continuity": {"sum_local": 0.0},
        },
        "postprocess": {
            "pressure": {"pressure_drop_kinematic_m2_s2": 1.0},
            "wall": {"sample_count": 5},
            "field_stats": {"velocity_finite": True},
        },
    }

    result = validate_runtime_metrics(metrics, config, Path("_results/openfoam/c03_missing"))

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "solver.final_residual_threshold" in failed
