from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.dam_break_vof_free_surface.config import (
    load_case_config,
    validate_case_config,
)


def test_openfoam_c06_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/dam_break_vof_free_surface").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.dam_break_vof_free_surface"
        assert config["solver"]["name"] == "interFoam"


def test_openfoam_c06_schema_rejects_unknown_geometry_key() -> None:
    config = yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["geometry"]["unexpected_length_m"] = 1.0

    with pytest.raises(ValueError, match="unexpected_length_m"):
        validate_case_config(config)


def test_openfoam_c06_schema_rejects_unknown_validation_gate() -> None:
    config = yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["validation"]["gate"] = "nearly_double_v"

    with pytest.raises(ValueError, match="nearly_double_v"):
        validate_case_config(config)
