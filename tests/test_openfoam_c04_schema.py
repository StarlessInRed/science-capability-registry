from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.config import (
    load_case_config,
    validate_case_config,
)


def test_openfoam_c04_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/external_aero_motorbike_rans_snappy").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.external_aero_motorbike_rans_snappy"
        assert config["solver"]["name"] == "simpleFoam"
        assert config["mesh"]["generator"] == "blockMesh_surfaceFeatureExtract_snappyHexMesh"
        if config["postprocess"]["force_extraction_source"] == "not_required":
            assert config["function_objects"]["force_coefficients"]["enabled"] is False
            assert config["function_objects"]["y_plus"]["required"] is False
        else:
            assert config["function_objects"]["force_coefficients"]["enabled"] is True
            assert config["function_objects"]["y_plus"]["required"] is True


def test_openfoam_c04_runtime_smoke_config_targets_wsl_v2112() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112.yaml")

    assert config["case_id"] == "runtime_smoke_wsl_v2112"
    assert config["backend"]["type"] == "wsl"
    assert config["validation"]["gate"] == "smoke"
    assert config["openfoam"]["runtime_profile"] == "openfoam_com_v2112"
    commands = "\n".join(config["solver"]["command_sequence"])
    for expected in ["snappyHexMesh", "checkMesh", "simpleFoam", "postProcess -latestTime -func yPlus"]:
        assert expected in commands


def test_openfoam_c04_solver_only_config_disables_native_postprocess() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_solver_only_wsl_v2112.yaml")

    assert config["case_id"] == "runtime_solver_only_wsl_v2112"
    assert config["postprocess"]["force_extraction_source"] == "not_required"
    assert config["function_objects"]["force_coefficients"]["enabled"] is False
    assert config["function_objects"]["y_plus"]["required"] is False
    commands = "\n".join(config["solver"]["command_sequence"])
    assert "simpleFoam" in commands
    assert "postProcess -latestTime -func yPlus" not in commands


def test_openfoam_c04_layer0_solver_only_config_disables_layers() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_solver_only_wsl_v2112.yaml")

    assert config["case_id"] == "runtime_layer0_solver_only_wsl_v2112"
    assert config["mesh"]["snappy"]["add_layers"] is False
    assert config["mesh"]["snappy"]["n_surface_layers"] == 0
    assert config["numerics"]["control"]["end_time_iterations"] == 5
    assert config["function_objects"]["force_coefficients"]["enabled"] is False


def test_openfoam_c04_schema_rejects_unknown_top_level_key() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    config["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        validate_case_config(config)


def test_openfoam_c04_schema_rejects_wrong_solver() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    config["solver"] = {**config["solver"], "name": "pimpleFoam"}

    with pytest.raises(ValueError, match="simpleFoam"):
        validate_case_config(config)


def test_openfoam_c04_schema_requires_mesh_quality_thresholds() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    config["mesh"] = {**config["mesh"], "quality": {**config["mesh"]["quality"]}}
    del config["mesh"]["quality"]["max_skewness"]

    with pytest.raises(ValueError, match="max_skewness"):
        validate_case_config(config)


def test_openfoam_c04_schema_requires_force_and_yplus_contracts() -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    config["function_objects"] = {**config["function_objects"]}
    del config["function_objects"]["force_coefficients"]

    with pytest.raises(ValueError, match="force_coefficients"):
        validate_case_config(config)

    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    config["function_objects"] = {**config["function_objects"]}
    del config["function_objects"]["y_plus"]

    with pytest.raises(ValueError, match="y_plus"):
        validate_case_config(config)


def test_openfoam_c04_asset_records_package_skeleton_status() -> None:
    asset = yaml.safe_load(Path("software/openfoam/assets/C04_external_aero_motorbike_rans_snappy.yaml").read_text(encoding="utf-8"))
    assert asset["benchmark_status"] == "package_skeleton_created"
    assert asset["card_status"] == "review"
