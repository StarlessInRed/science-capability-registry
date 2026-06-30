from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.config import load_case_config
from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.runner import run
from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.validation import (
    validate_manifest,
    validate_runtime_metrics,
)


def test_openfoam_c04_manifest_rejects_missing_snappy_dict(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    manifest = run(config=config, output_dir=tmp_path, dry_run=True)
    manifest["generated_files"] = [path for path in manifest["generated_files"] if path != "case/system/snappyHexMeshDict"]

    validation = validate_manifest(manifest, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "generated_file.listed.case/system/snappyHexMeshDict" in failed


def test_openfoam_c04_manifest_rejects_missing_checkmesh_command(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    manifest = run(config=config, output_dir=tmp_path, dry_run=True)
    manifest["solver_commands"] = [command for command in manifest["solver_commands"] if "checkMesh" not in command]

    validation = validate_manifest(manifest, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "solver_commands.checkMesh" in failed


def test_openfoam_c04_manifest_rejects_disabled_force_coefficients(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    manifest = run(config=config, output_dir=tmp_path, dry_run=True)
    bad_config = {**config, "function_objects": {**config["function_objects"], "force_coefficients": {**config["function_objects"]["force_coefficients"], "enabled": False}}}

    validation = validate_manifest(manifest, bad_config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "forceCoeffs.enabled" in failed


def test_openfoam_c04_runtime_metrics_synthetic_pass(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    for rel_path in config["outputs"]["expected_outputs"]:
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "mesh": {"snappy_completed": True, "mesh_ok": True, "cell_count": 10000, "max_non_orthogonality": 50.0, "max_skewness": 2.0},
        "solver": {"started": True, "fatal_error_detected": False, "max_final_residual": 0.0001},
        "postprocess": {
            "force_coefficients": {"available": True, "cd_tail_mean": 0.32, "cl_tail_mean": 0.05, "cd_tail_std": 0.01, "cl_tail_std": 0.01},
            "y_plus": {"available": True, "min": 40.0, "max": 120.0, "mean": 80.0},
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    assert validation["passed"] is True


def test_openfoam_c04_runtime_metrics_rejects_mesh_force_and_yplus_failures(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 1 if "snappyHexMesh" in command else 0} for command in config["solver"]["command_sequence"]]},
        "mesh": {"snappy_completed": False, "mesh_ok": False, "cell_count": 10, "max_non_orthogonality": 90.0, "max_skewness": 9.0},
        "solver": {"started": True, "fatal_error_detected": True, "max_final_residual": 1.0},
        "postprocess": {
            "force_coefficients": {"available": False},
            "y_plus": {"available": False},
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "mesh.snappy_completed" in failed
    assert "mesh.checkMesh_ok" in failed
    assert "solver.no_fatal_error" in failed
    assert "force.available" in failed
    assert "yPlus.available" in failed
