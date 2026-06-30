from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.config import (
    load_case_config,
    validate_case_config,
)


CONFIG_PATH = Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml")


def _baseline_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_openfoam_c07_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/conjugate_heat_transfer_cooling").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.conjugate_heat_transfer_cooling"
        assert config["openfoam"]["runtime_profile"] == "openfoam_com_v2112_cht"
        assert config["openfoam"]["case_layout"] == "legacy_cht_multi_region"
        assert config["solver"]["name"] == "chtMultiRegionSimpleFoam"
        assert config["regions"]["fluid"] == ["domain0"]
        assert config["regions"]["solid"] == ["v_CPU", "v_fins"]


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
    config["regions"]["solid"] = ["v_CPU"]

    with pytest.raises(ValueError, match="regions.solid"):
        validate_case_config(config)
