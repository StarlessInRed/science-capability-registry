from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.validation import (
    validate_manifest,
    validate_runtime_metrics,
)


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/transient_cylinder_vortex_shedding/baseline_cylinder2d.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_openfoam_c05_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline_cylinder2d.yaml",
        "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
        "backend": {"type": "dry_run_only"},
        "solver": {"name": "pimpleFoam"},
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "fields": config["fields"],
        "numerics": config["numerics"],
        "function_objects": config["function_objects"],
        "expected_outputs": [],
        "validation_targets": {},
        "generated_files": ["case/0/U"],
    }

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/p" in failed


def test_openfoam_c05_validation_rejects_disabled_force_coefficients() -> None:
    config = _baseline_config()
    manifest = {
        section: config[section]
        for section in ["backend", "solver", "template", "geometry", "mesh", "material", "fields", "numerics", "function_objects"]
    }
    manifest.update(
        {
            "source_config": "baseline_cylinder2d.yaml",
            "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
            "expected_outputs": config["outputs"]["expected_outputs"],
            "validation_targets": config["validation"],
            "generated_files": list(config["validation"]["required_generated_files"]),
        }
    )
    manifest["function_objects"] = {"force_coefficients": {**config["function_objects"]["force_coefficients"], "enabled": False}}

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "function_object.force_coefficients_enabled" in failed


def test_openfoam_c05_validation_allows_disabled_function_object_for_python_proxy() -> None:
    config = _baseline_config()
    config["postprocess"]["force_extraction_source"] = "python_patch_surface_proxy"
    manifest = {
        section: config[section]
        for section in ["backend", "solver", "template", "geometry", "mesh", "material", "fields", "numerics", "function_objects"]
    }
    manifest.update(
        {
            "source_config": "baseline_cylinder2d.yaml",
            "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
            "expected_outputs": config["outputs"]["expected_outputs"],
            "validation_targets": config["validation"],
            "generated_files": list(config["validation"]["required_generated_files"]),
        }
    )
    manifest["function_objects"] = {"force_coefficients": {**config["function_objects"]["force_coefficients"], "enabled": False}}

    result = validate_manifest(manifest, config)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "function_object.force_coefficients_enabled" not in failed


def test_openfoam_c05_runtime_validation_rejects_wrong_force_source(tmp_path: Path) -> None:
    config = _baseline_config()
    config["postprocess"]["force_extraction_source"] = "python_patch_surface_proxy"
    config["postprocess"]["strouhal_estimate"] = False
    config["validation"]["force_coefficients_required"] = True
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_s"],
            "max_courant_number": 0.1,
            "residual_history": [{"final": 1e-6}],
        },
        "postprocess": {
            "force_coefficients": {
                "available": True,
                "source": "openfoam_forceCoeffs",
            }
        },
    }

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.force_coefficients_source" in failed


def test_openfoam_c05_runtime_validation_checks_strouhal_target_range(tmp_path: Path) -> None:
    config = _baseline_config()
    config["postprocess"]["force_extraction_source"] = "python_patch_surface_proxy"
    config["postprocess"]["strouhal_estimate"] = True
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_s"],
            "max_courant_number": 0.1,
            "residual_history": [{"final": 1e-6}],
        },
        "postprocess": {
            "force_coefficients": {
                "available": True,
                "source": "python_patch_surface_proxy",
            },
            "strouhal": {
                "available": True,
                "strouhal_number": 0.5,
            },
        },
    }

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.strouhal_target_range" in failed


def test_openfoam_c05_runtime_validation_checks_force_series_quality(tmp_path: Path) -> None:
    config = _baseline_config()
    config["postprocess"]["force_extraction_source"] = "python_patch_surface_proxy"
    config["postprocess"]["strouhal_estimate"] = True
    config["validation"]["min_force_samples"] = 60
    config["validation"]["min_force_time_span_s"] = 20
    config["validation"]["min_lift_peak_count"] = 3
    config["validation"]["max_period_cv"] = 0.3
    config["validation"]["min_cl_amplitude"] = 0.001
    config["outputs"]["expected_outputs"] = []
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_s"],
            "max_courant_number": 0.1,
            "residual_history": [{"final": 1e-6}],
        },
        "postprocess": {
            "force_coefficients": {
                "available": True,
                "source": "python_patch_surface_proxy",
                "row_count": 4,
                "time_span_s": 1.0,
                "nonfinite_count": 0,
            },
            "strouhal": {
                "available": True,
                "strouhal_number": 0.2,
                "peak_count": 2,
                "period_cv": 0.4,
                "cl_amplitude": 0.0001,
            },
        },
    }

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.force_sample_count" in failed
    assert "postprocess.force_time_span" in failed
    assert "postprocess.strouhal_peak_count" in failed
    assert "postprocess.strouhal_period_cv" in failed
    assert "postprocess.strouhal_lift_amplitude" in failed


def test_openfoam_c05_runtime_validation_allows_final_time_step_tolerance(tmp_path: Path) -> None:
    config = _baseline_config()
    config["postprocess"]["strouhal_estimate"] = False
    config["validation"]["force_coefficients_required"] = False
    config["outputs"]["expected_outputs"] = []
    final_time = config["numerics"]["control"]["end_time_s"] - config["numerics"]["control"]["delta_t_s"] / 2.0
    metrics = {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in config["solver"]["command_sequence"]]},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": final_time,
            "max_courant_number": 0.1,
            "residual_history": [{"final": 1e-6}],
        },
        "postprocess": {},
    }

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "solver.final_time" not in failed
