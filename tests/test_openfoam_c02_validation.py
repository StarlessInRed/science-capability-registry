from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation.validation import (
    validate_manifest,
    validate_runtime_metrics,
)


def _baseline_config() -> dict:
    return yaml.safe_load(Path("configs/openfoam/potential_flow_cylinder_analytical_validation/baseline.yaml").read_text(encoding="utf-8"))


def _valid_manifest(config: dict) -> dict:
    return {
        "source_config": "baseline.yaml",
        "schema_id": "schemas/openfoam_C02_potential_flow_cylinder_analytical_validation.schema.json",
        "backend": {"type": "dry_run_only"},
        "solver": {"name": "potentialFoam"},
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "fields": config["fields"],
        "numerics": config["numerics"],
        "analytical_reference": config["analytical_reference"],
        "function_objects": config["function_objects"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "generated_files": list(config["validation"]["required_generated_files"]),
        "mesh_commands": ["blockMesh"],
        "solver_commands": config["solver"]["command_sequence"],
    }


def test_openfoam_c02_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = _valid_manifest(config)
    manifest["generated_files"] = ["case/0/U"]

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/p" in failed


def test_openfoam_c02_validation_rejects_wrong_template_path() -> None:
    config = _baseline_config()
    config["template"]["source_path"] = "/opt/OpenFOAM-v2112/tutorials/incompressible/simpleFoam/pitzDaily"
    manifest = _valid_manifest(config)

    result = validate_manifest(manifest, config)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "template.official_cylinder" in failed


def test_openfoam_c02_validation_rejects_missing_sample_set() -> None:
    config = _baseline_config()
    config["postprocess"]["sample_sets"] = ["cylinder_patch_owner_cells"]
    manifest = _valid_manifest(config)

    result = validate_manifest(manifest, config)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.sample_sets.field" in failed


def test_openfoam_c02_runtime_validation_checks_analytical_thresholds(tmp_path: Path) -> None:
    config = _baseline_config()
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "residual_history": [{"field": "Phi", "final": 1e-8}],
        },
        "postprocess": {
            "analytical": {
                "field": {
                    "available": True,
                    "velocity_l2_error": 0.01,
                    "velocity_linf_error": 0.02,
                    "pressure_l2_error": 0.01,
                },
                "surface_cp": {
                    "available": True,
                    "cp_linf_error": 2.0,
                },
            }
        },
    }

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.cp_linf_error" in failed
