from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.validation import (
    validate_manifest,
)
from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.runtime import (
    validate_runtime_metrics,
)


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml").read_text(
            encoding="utf-8"
        )
    )


def _mhr_config() -> dict:
    return yaml.safe_load(
        Path(
            "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml"
        ).read_text(encoding="utf-8")
    )


def _manifest(config: dict) -> dict:
    return {
        "source_config": "baseline_cpu_cabinet_wsl_v2112.yaml",
        "schema_id": "schemas/openfoam_C07_conjugate_heat_transfer_cooling.schema.json",
        "runtime_profile": "openfoam_com_v2112_cht",
        "backend": {"type": "dry_run_only"},
        "regions": config["regions"],
        "solver": {"name": "chtMultiRegionSimpleFoam"},
        "generated_files": list(config["validation"]["required_generated_files"]),
        "mesh_commands": list(config["mesh_workflow"]["command_sequence"]),
        "radiation_commands": list(config["radiation"]["preprocessing_commands"]),
        "solver_commands": list(config["solver"]["command_sequence"]),
        "postprocess_commands": ["python:write_region_temperature_summary"],
        "expected_outputs": [],
        "validation_targets": {},
        "interfaces": list(config["validation"]["required_interface_pairs"]),
    }


def test_openfoam_c07_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = _manifest(config)
    manifest["generated_files"] = ["case/constant/regionProperties"]

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/domain0/T" in failed


def test_openfoam_c07_validation_rejects_missing_interface_pair() -> None:
    config = _baseline_config()
    manifest = _manifest(config)
    manifest["interfaces"] = ["domain0_to_v_CPU"]

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "interface_pair.planned.domain0_to_v_fins" in failed
    assert "interface_pair.planned.v_CPU_to_v_fins" in failed


def test_openfoam_c07_validation_rejects_missing_radiation_command() -> None:
    config = _mhr_config()
    manifest = _manifest(config)
    manifest["radiation_commands"] = ["faceAgglomerate -region bottomAir"]

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "radiation_command.planned.viewFactorsGen -region topAir" in failed


def _promotion_metrics(config: dict) -> dict:
    regions = [*config["regions"]["fluid"], *config["regions"]["solid"]]
    commands = [
        *config["mesh_workflow"]["command_sequence"],
        *config["radiation"]["preprocessing_commands"],
        *config["solver"]["command_sequence"],
        *[command for command in config["postprocess"]["command_sequence"] if not command.startswith("python:")],
    ]
    return {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in commands]},
        "mesh": {"mesh_ok": True},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": config["numerics"]["control"]["end_time_iterations"],
            "regions_seen": regions,
            "last_residuals": {region: {"T": {"final": 1e-6}} for region in regions},
        },
        "postprocess": {
            "temperatures": {
                "regions": [
                    {"region": region, "available": True, "finite": True, "min_T_K": 300.0, "max_T_K": 400.0}
                    for region in regions
                ]
            },
            "interfaces": {"available": True},
            "patch_heat_flux_proxy": {"available": True},
            "interface_heat_flux_field": {
                "available": True,
                "max_relative_heat_rate_mismatch": 0.1,
                "interfaces": [{"interface": config["interfaces"][0]["name"], "relative_heat_rate_mismatch": 0.1}],
            },
        },
    }


def test_openfoam_c07_runtime_validation_rejects_proxy_only_heat_flux_for_promotion(tmp_path: Path) -> None:
    config = _mhr_config()
    config["validation"]["gate"] = "targeted-regression"
    config["outputs"]["expected_outputs"] = []
    config["radiation"]["required_generated_files"] = []
    config["postprocess"]["heat_flux_validation"] = {
        "source": "proxy_only",
        "native_required_for_promotion": True,
        "energy_balance_source": "not_configured",
    }
    metrics = _promotion_metrics(config)

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.native_heat_flux_required_for_promotion" in failed
    assert "postprocess.energy_balance_required_for_promotion" in failed
    assert "postprocess.heat_flux_parity_required_for_promotion" in failed


def test_openfoam_c07_runtime_validation_rejects_bare_face_field_heat_flux_for_promotion(tmp_path: Path) -> None:
    config = _mhr_config()
    config["validation"]["gate"] = "targeted-regression"
    config["outputs"]["expected_outputs"] = []
    config["radiation"]["required_generated_files"] = []
    metrics = _promotion_metrics(config)

    result = validate_runtime_metrics(metrics, config, tmp_path)

    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "postprocess.heat_flux_parity_required_for_promotion" in failed


def test_openfoam_c07_runtime_validation_accepts_cross_validated_face_field_heat_flux_for_promotion(tmp_path: Path) -> None:
    config = _mhr_config()
    config["validation"]["gate"] = "targeted-regression"
    config["outputs"]["expected_outputs"] = []
    config["radiation"]["required_generated_files"] = []
    config["postprocess"]["heat_flux_validation"] = {
        **config["postprocess"]["heat_flux_validation"],
        "evidence_role": "promotion_candidate",
        "parity_status": "passed",
        "parity_source_type": "external_reference",
        "parity_evidence_id": "reviewed_heat_flux_parity_reference",
    }
    metrics = _promotion_metrics(config)

    result = validate_runtime_metrics(metrics, config, tmp_path)

    assert result["passed"] is True
