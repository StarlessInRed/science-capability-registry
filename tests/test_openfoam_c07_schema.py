from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.config import (
    load_case_config,
    validate_case_config,
)


CONFIG_PATH = Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml")
MHR_CONFIG_PATH = Path(
    "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml"
)
MHR_V2412_CONFIG_PATH = Path(
    "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2412.yaml"
)


def _baseline_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_openfoam_c07_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/conjugate_heat_transfer_cooling").glob("*.yaml"))
    assert paths
    profiles = set()
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.conjugate_heat_transfer_cooling"
        assert config["openfoam"]["runtime_profile"] in {"openfoam_com_v2112_cht", "openfoam_com_v2412_cht"}
        assert config["openfoam"]["case_layout"] == "legacy_cht_multi_region"
        assert config["solver"]["name"] == "chtMultiRegionSimpleFoam"
        assert config["regions"]["fluid"]
        assert config["regions"]["solid"]
        heat_flux = config["postprocess"]["heat_flux_validation"]
        assert heat_flux["promotion_policy"] == "native_or_independent_heat_flux_parity_required"
        assert heat_flux["evidence_role"] == "mitigation_only"
        profiles.add(config["template"]["source_profile_key"])
    assert {"c07_cpu_cabinet", "c07_multi_region_heater_radiation"}.issubset(profiles)


def test_openfoam_c07_schema_rejects_unknown_top_level_key() -> None:
    config = _baseline_config()
    config["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        validate_case_config(config)


def test_openfoam_c07_schema_rejects_single_region_profile() -> None:
    config = _baseline_config()
    config["openfoam"]["runtime_profile"] = "openfoam_com_v2112"
    config["openfoam"]["case_layout"] = "single_region"

    with pytest.raises(ValueError, match="runtime_profile"):
        validate_case_config(config)


def test_openfoam_c07_schema_rejects_missing_solid_region() -> None:
    config = _baseline_config()
    config["regions"]["solid"] = []

    with pytest.raises(ValueError, match="regions.solid"):
        validate_case_config(config)


def test_openfoam_c07_schema_accepts_multi_region_heater_radiation_profile() -> None:
    config = load_case_config(MHR_CONFIG_PATH)

    assert config["template"]["source_profile_key"] == "c07_multi_region_heater_radiation"
    assert config["regions"]["fluid"] == ["bottomAir", "topAir"]
    assert config["regions"]["solid"] == ["heater", "leftSolid", "rightSolid"]
    assert config["radiation"]["enabled"] is True
    assert "faceAgglomerate -region bottomAir" in config["radiation"]["preprocessing_commands"]
    assert config["heat_sources"]["heater"]["source_type"] == "fixed_temperature_boundary"
    assert config["mesh_workflow"]["block_mesh_cells"] == [30, 10, 10]
    assert config["postprocess"]["patch_heat_flux_proxy_summary"] is True
    assert config["postprocess"]["interface_heat_flux_field_summary"] is True
    assert config["postprocess"]["heat_flux_validation"]["source"] == "face_field_integration"
    assert config["postprocess"]["heat_flux_validation"]["parity_status"] == "not_configured"


def test_openfoam_c07_schema_accepts_v2412_heater_radiation_viewfactors_path() -> None:
    config = load_case_config(MHR_V2412_CONFIG_PATH)

    assert config["openfoam"]["runtime_profile"] == "openfoam_com_v2412_cht"
    assert config["radiation"]["preprocessing_commands"] == [
        "viewFactorsGen -region bottomAir",
        "viewFactorsGen -region topAir",
    ]
    assert "chtMultiRegionSimpleFoam -postProcess -region bottomAir -func wallHeatFlux -latestTime" in config[
        "postprocess"
    ]["command_sequence"]
    assert "postProcess -region bottomAir -func wallHeatFlux -latestTime" not in config["postprocess"]["command_sequence"]
    assert "case/constant/bottomAir/mapDist" in config["radiation"]["required_generated_files"]
    assert "case/0/bottomAir/facesAgglomeration" not in config["radiation"]["required_generated_files"]


def test_openfoam_c07_schema_accepts_heater_radiation_perturbation_matrix_configs() -> None:
    paths = sorted(Path("configs/openfoam/conjugate_heat_transfer_cooling").glob("perturb_*_wsl_v2112.yaml"))
    configs = [load_case_config(path) for path in paths]
    roles = {config["validation"]["matrix_role"] for config in configs}

    assert roles == {"heater_temperature_high", "airflow_high", "mesh_refinement"}
    assert any("velocity_overrides_m_s" in config["fields"] for config in configs)
    assert any(config["mesh_workflow"]["block_mesh_cells"] == [36, 12, 12] for config in configs)
