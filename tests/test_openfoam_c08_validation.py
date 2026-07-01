from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.config import load_case_config
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.runner import run
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.validation import (
    validate_manifest,
    validate_runtime_metrics,
)


def _owner_cell_conservation(mass: float = 0.0, energy: float = 0.0) -> dict:
    return {
        "owner_cell_proxy": {
            "available": True,
            "method": "boundary_flux_owner_cell_proxy",
            "boundary_flux_mass_imbalance_proxy": mass,
            "boundary_flux_total_energy_imbalance_proxy": energy,
        },
        "flux_parity": {
            "available": False,
            "method": "not_configured",
        },
    }


def test_openfoam_c08_manifest_rejects_missing_required_generated_file(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    manifest = run(config=config, output_dir=tmp_path, dry_run=True)
    manifest["generated_files"] = [path for path in manifest["generated_files"] if path != "case/0/T"]

    validation = validate_manifest(manifest, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "generated_file.listed.case/0/T" in failed


def test_openfoam_c08_manifest_rejects_wrong_template(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    manifest = run(config=config, output_dir=tmp_path, dry_run=True)
    bad_config = {**config, "template": {**config["template"], "source_path": "/opt/OpenFOAM-v2112/tutorials/incompressible/icoFoam/cavity/cavity"}}

    validation = validate_manifest(manifest, bad_config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "template.official_forwardStep" in failed


def test_openfoam_c08_runtime_metrics_synthetic_pass(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    for rel_path in config["outputs"]["expected_outputs"]:
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.1, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 5.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 2.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 1.2,
                "pressure_jump_ratio": 5.0,
                "density_jump_ratio": 3.0,
            },
            "conservation": _owner_cell_conservation(),
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    assert validation["passed"] is True


def test_openfoam_c08_runtime_metrics_rejects_fatal_and_bad_fields(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    metrics = {
        "runtime": {"commands": [{"command": "blockMesh", "returncode": 0}, {"command": "checkMesh", "returncode": 0}, {"command": "rhoCentralFoam", "returncode": 1}]},
        "solver": {"started": True, "fatal_error_detected": True, "max_courant": 1.0, "final_time_s": 0.1},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": -1.0},
                "T": {"available": True, "finite": False, "min": 0.0},
                "rho": {"available": False, "finite": False},
                "U": {"available": True, "finite": False},
            },
            "shock": {"available": False},
            "conservation": {"available": False},
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "solver.no_fatal_error" in failed
    assert "solver.max_courant" in failed
    assert "field.p.positive_finite" in failed
    assert "postprocess.shock.available" in failed
    assert "boundary_flux.mass_imbalance_proxy" in failed
    assert "boundary_flux.total_energy_imbalance_proxy" in failed


def test_openfoam_c08_runtime_metrics_rejects_non_shock_jump_ratios(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.1, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 5.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 2.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 1.2,
                "pressure_jump_ratio": 0.9,
                "density_jump_ratio": 0.8,
            },
            "conservation": _owner_cell_conservation(),
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "postprocess.pressure_jump_ratio_sanity" in failed
    assert "postprocess.density_jump_ratio_sanity" in failed


def test_openfoam_c08_runtime_metrics_requires_reference_and_native_flux_for_promotion(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["validation"]["gate"] = "integration"
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.1, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 5.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 2.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 1.2,
                "pressure_jump_ratio": 5.0,
                "density_jump_ratio": 3.0,
            },
            "conservation": _owner_cell_conservation(),
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)
    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "postprocess.shock_reference_required_for_promotion" in failed
    assert "boundary_flux.native_or_face_flux_parity_required_for_promotion" in failed


def test_openfoam_c08_runtime_metrics_rejects_smoke_reference_for_promotion(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml")
    config["validation"]["gate"] = "integration"
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.09, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 10.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 3.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 0.425,
                "pressure_jump_ratio": 7.623675555555555,
                "density_jump_ratio": 3.2820011603091723,
            },
            "conservation": _owner_cell_conservation(),
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "postprocess.shock_reference_required_for_promotion" not in failed
    assert "postprocess.shock_reference_provenance_required_for_promotion" in failed
    assert "boundary_flux.native_or_face_flux_parity_required_for_promotion" in failed


def test_openfoam_c08_runtime_metrics_accepts_independent_reference_and_face_flux_parity_for_promotion(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml")
    config["validation"]["gate"] = "integration"
    config["outputs"]["expected_outputs"] = []
    config["shock_reference"]["source_type"] = "independent_reference"
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.09, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 10.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 3.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 0.425,
                "pressure_jump_ratio": 7.623675555555555,
                "density_jump_ratio": 3.2820011603091723,
            },
            "conservation": {
                "owner_cell_proxy": {
                    "available": True,
                    "method": "boundary_flux_owner_cell_proxy",
                    "boundary_flux_mass_imbalance_proxy": 0.0,
                    "boundary_flux_total_energy_imbalance_proxy": 0.0,
                },
                "flux_parity": {
                    "available": True,
                    "method": "face_field_integration",
                    "boundary_flux_mass_imbalance": 0.0,
                    "boundary_flux_total_energy_imbalance": 0.0,
                },
            },
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    assert validation["passed"] is True


def test_openfoam_c08_runtime_metrics_rejects_local_regression_baseline_for_promotion(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml")
    config["validation"]["gate"] = "integration"
    config["outputs"]["expected_outputs"] = []
    config["shock_reference"]["accepted_baseline_samples"]["status"] = "accepted_regression_baseline"
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.09, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 10.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 3.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 0.425,
                "pressure_jump_ratio": 7.623675555555555,
                "density_jump_ratio": 3.2820011603091723,
            },
            "conservation": _owner_cell_conservation(),
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "postprocess.shock_reference_provenance_required_for_promotion" in failed


def test_openfoam_c08_runtime_metrics_rejects_bad_face_flux_parity_for_promotion(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml")
    config["validation"]["gate"] = "integration"
    config["outputs"]["expected_outputs"] = []
    config["shock_reference"]["source_type"] = "independent_reference"
    conservation = _owner_cell_conservation()
    conservation["flux_parity"] = {
        "available": True,
        "method": "face_field_integration",
        "boundary_flux_mass_imbalance": 1.0,
        "boundary_flux_total_energy_imbalance": 1.0,
    }
    metrics = {
        "runtime": {
            "commands": [
                {"command": "blockMesh", "returncode": 0},
                {"command": "checkMesh", "returncode": 0},
                {"command": "rhoCentralFoam", "returncode": 0},
            ]
        },
        "solver": {"started": True, "fatal_error_detected": False, "max_courant": 0.09, "final_time_s": 4.0},
        "postprocess": {
            "field_extrema": {
                "p": {"available": True, "finite": True, "min": 0.5, "max": 10.0},
                "T": {"available": True, "finite": True, "min": 0.5, "max": 3.0},
                "rho": {"available": True, "finite": True, "min": 0.5, "max": 4.0},
                "U": {"available": True, "finite": True, "min": 0.0, "max": 3.0},
            },
            "shock": {
                "available": True,
                "shock_position_m": 0.425,
                "pressure_jump_ratio": 7.623675555555555,
                "density_jump_ratio": 3.2820011603091723,
            },
            "conservation": conservation,
        },
    }

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {item["name"] for item in validation["checks"] if not item["passed"]}
    assert "boundary_flux.native_or_face_flux_parity_required_for_promotion" in failed
