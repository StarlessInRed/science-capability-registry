from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.validation import (
    validate_manifest,
)


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml").read_text(
            encoding="utf-8"
        )
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
