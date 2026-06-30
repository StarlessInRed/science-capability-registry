from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow.config import load_case_config


def test_openfoam_c03_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/backward_facing_step_rans_internal_flow").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.backward_facing_step_rans_internal_flow"
        assert config["solver"]["name"] == "simpleFoam"
