from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.config import (
    load_case_config,
    validate_case_config,
)


def test_openfoam_c08_configs_match_schema() -> None:
    paths = sorted(Path("configs/openfoam/compressible_shock_capturing_forward_step").glob("*.yaml"))
    assert paths
    for path in paths:
        config = load_case_config(path)
        assert config["capability_id"] == "cfd.openfoam.compressible_shock_capturing_forward_step"
        assert config["solver"]["name"] == "rhoCentralFoam"
        assert config["fields"]["rho"]["source"] == "derived_from_thermophysical_state"
        if path.name == "baseline.yaml":
            assert config["validation"]["gate"] == "static-readiness"
        if path.name == "cfl_reduced.yaml":
            assert config["validation"]["gate"] == "smoke"
            assert config["shock_reference"]["source_type"] == "local_runtime_smoke"
            assert config["shock_reference"]["source_url_or_path"].startswith("reports/")
            assert config["shock_reference"]["extraction_method"] == "local_runtime_python_pressure_density_gradient"
            assert config["shock_reference"]["review_status"] == "local_smoke_only"
            assert config["shock_reference"]["accepted_baseline_samples"]["status"] == "smoke_reference_only"
            assert config["shock_reference"]["flux_parity_policy"] == "native_or_face_flux_required_for_promotion"


def test_openfoam_c08_schema_rejects_unknown_top_level_key() -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        validate_case_config(config)


def test_openfoam_c08_schema_rejects_wrong_solver() -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["solver"] = {**config["solver"], "name": "rhoCentralFoamPlus"}

    with pytest.raises(ValueError, match="rhoCentralFoam"):
        validate_case_config(config)


def test_openfoam_c08_schema_rejects_invalid_gate_name() -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["validation"] = {**config["validation"], "gate": "shock-smoke"}

    with pytest.raises(ValueError, match="shock-smoke"):
        validate_case_config(config)


def test_openfoam_c08_schema_rejects_legacy_conservation_threshold_keys() -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["validation"] = {
        **config["validation"],
        "max_mass_conservation_error": 0.02,
    }

    with pytest.raises(ValueError, match="max_mass_conservation_error"):
        validate_case_config(config)


def test_openfoam_c08_asset_records_case_freeze_status() -> None:
    asset = yaml.safe_load(Path("software/openfoam/assets/C08_compressible_shock_capturing_forward_step.yaml").read_text(encoding="utf-8"))
    assert asset["benchmark_status"] == "benchmark_validated"
    assert asset["benchmark"]["case_freeze"]["status"] == "benchmark_validated_for_local_case_freeze"
    assert asset["card_status"] == "review"
