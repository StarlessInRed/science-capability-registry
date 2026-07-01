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
        assert config["validation"]["sampling_parity"]["status"] == "profile_disabled"
        assert config["validation"]["full_horizon"]["status"] == "short_horizon_only"
        assert config["validation"]["reference_policy"]["status"] == "not_selected"


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


def test_openfoam_c06_schema_rejects_double_v_without_sampling_full_horizon_reference() -> None:
    config = yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["validation"]["gate"] = "double-v"

    with pytest.raises(ValueError, match="sampling_parity"):
        validate_case_config(config)


def test_openfoam_c06_schema_accepts_double_v_only_with_required_policy_evidence() -> None:
    config = yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["validation"]["gate"] = "double-v"
    config["validation"]["sampling_parity"] = {
        "required_for_gate": True,
        "status": "passed",
        "source": "native_openfoam_sampling",
        "native_sampling_enabled": True,
        "evidence_id": "candidate_native_sampling_parity",
    }
    config["validation"]["full_horizon"] = {
        "required_for_gate": True,
        "status": "passed",
        "end_time_s": 1.0,
        "reference_horizon_s": 1.0,
        "evidence_id": "candidate_full_horizon_front_position",
    }
    config["validation"]["reference_policy"] = {
        "required_for_gate": True,
        "status": "passed",
        "source_type": "external_benchmark",
        "comparison_quantity": "front_position",
        "target_change_policy": "reviewed_reference_required",
        "evidence_id": "candidate_external_dam_break_reference",
    }

    validated = validate_case_config(config)

    assert validated["validation"]["gate"] == "double-v"
