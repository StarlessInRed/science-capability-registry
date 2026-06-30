from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation.config import (
    load_case_config,
    validate_case_config,
)


def test_openfoam_c02_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/potential_flow_cylinder_analytical_validation").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.potential_flow_cylinder_analytical_validation"
        assert config["solver"]["name"] == "potentialFoam"
        assert config["analytical_reference"]["surface_cp_formula"] == "Cp(theta) = 1 - 4*sin(theta)^2"


def test_openfoam_c02_schema_rejects_unknown_top_level_key() -> None:
    config = load_case_config("configs/openfoam/potential_flow_cylinder_analytical_validation/baseline.yaml")
    config["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        validate_case_config(config)


def test_openfoam_c02_schema_rejects_wrong_solver() -> None:
    config = load_case_config("configs/openfoam/potential_flow_cylinder_analytical_validation/baseline.yaml")
    config["solver"] = {**config["solver"], "name": "simpleFoam"}

    with pytest.raises(ValueError, match="potentialFoam"):
        validate_case_config(config)


def test_openfoam_c02_asset_records_package_skeleton_status() -> None:
    asset = yaml.safe_load(Path("software/openfoam/assets/C02_potential_flow_cylinder_analytical_validation.yaml").read_text(encoding="utf-8"))
    assert asset["benchmark_status"] == "package_skeleton_created"
    assert asset["card_status"] == "review"
