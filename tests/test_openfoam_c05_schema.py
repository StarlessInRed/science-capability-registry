from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator


SCHEMA_PATH = Path("schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json")
CONFIG_PATH = Path("configs/openfoam/transient_cylinder_vortex_shedding/baseline_cylinder2d.yaml")
CONFIG_DIR = CONFIG_PATH.parent
ASSET_PATH = Path("software/openfoam/assets/C05_transient_cylinder_vortex_shedding.yaml")
TASK_PATH = Path("tasks/openfoam_C05_transient_cylinder_vortex_shedding_intern_task.md")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_openfoam_c05_baseline_config_matches_schema() -> None:
    validator = Draft202012Validator(_schema())
    errors = sorted(validator.iter_errors(_config()), key=lambda error: list(error.path))
    assert not errors, [error.message for error in errors]


def test_openfoam_c05_all_configs_match_schema() -> None:
    validator = Draft202012Validator(_schema())
    failures = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(config), key=lambda error: list(error.path))
        if errors:
            failures[path.as_posix()] = [error.message for error in errors]

    assert not failures


def test_openfoam_c05_schema_accepts_v2412_native_forcecoeffs_smoke() -> None:
    config = yaml.safe_load(
        (CONFIG_DIR / "runtime_forcecoeffs_smoke_wsl_v2412.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(_schema()).iter_errors(config), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]
    assert config["openfoam"]["runtime_profile"] == "openfoam_com_v2412"
    assert config["postprocess"]["force_extraction_source"] == "openfoam_forceCoeffs"
    assert config["postprocess"]["strouhal_estimate"] is False


def test_openfoam_c05_all_configs_bind_strouhal_reference_policy() -> None:
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        policy = config["strouhal_reference_policy"]

        if policy["reference_policy"] == "reference_not_selected":
            assert config["validation"]["strouhal_target_range"] == [0.16, 0.24]
            assert policy["source_id"] == "openfoam_C05_strouhal_reference_policy_2026-07-01"
            assert policy["source_type"] == "policy_report"
            assert policy["target_change_policy"] == "do_not_relax_until_reference_selected"
        elif policy["reference_policy"] == "case_freeze_local_tutorial_baseline":
            assert config["validation"]["strouhal_target_range"] == [0.13, 0.15]
            assert policy["source_id"] == "openfoam_C05_v2412_native_forcecoeffs_strouhal_diagnostic_2026-07-01"
            assert policy["source_type"] == "local_runtime_evidence"
            assert policy["target_change_policy"] == "case_freeze_scope_update_required"
            assert policy["geometry_match_status"] == "official_tutorial_finite_domain"
        else:
            assert config["validation"]["strouhal_target_range"] == [0.16, 0.24]
            assert policy["source_id"] == "openfoam_C05_external_free_cylinder_reference_2026-07-01"
            assert policy["source_type"] == "external_benchmark"
            assert policy["target_change_policy"] == "reviewed_reference_update_required"
            assert policy["geometry_match_status"] == "comparable_free_cylinder"
            assert policy["reference_strouhal_range"][0] <= 0.16
            assert policy["reference_strouhal_range"][1] >= 0.24


def test_openfoam_c05_schema_accepts_external_reference_binding_config() -> None:
    config = yaml.safe_load(
        (CONFIG_DIR / "runtime_forcecoeffs_strouhal_external_reference_wsl_v2412.yaml").read_text(encoding="utf-8")
    )

    errors = sorted(Draft202012Validator(_schema()).iter_errors(config), key=lambda error: list(error.path))

    assert not errors, [error.message for error in errors]
    policy = config["strouhal_reference_policy"]
    assert policy["reference_policy"] == "external_reference_selected"
    assert policy["source_url_or_path"].startswith("https://")
    assert "St = fD/U" in policy["reference_definition"]
    assert config["postprocess"]["force_extraction_source"] == "openfoam_forceCoeffs"


def test_openfoam_c05_schema_rejects_relaxed_strouhal_target_without_reference() -> None:
    config = _config()
    config["validation"]["strouhal_target_range"] = [0.12, 0.16]

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("strouhal_target_range" in ".".join(str(part) for part in error.path) for error in errors)


def test_openfoam_c05_schema_rejects_untracked_top_level_key() -> None:
    config = _config()
    config["hidden_choice"] = True

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("Additional properties" in error.message for error in errors)


def test_openfoam_c05_assets_record_case_freeze_status() -> None:
    asset = yaml.safe_load(ASSET_PATH.read_text(encoding="utf-8"))
    task_text = TASK_PATH.read_text(encoding="utf-8")

    assert asset["integration_targets"]["input_schema"] == SCHEMA_PATH.as_posix()
    assert asset["benchmark_status"] == "benchmark_validated"
    assert asset["benchmark"]["case_freeze"]["status"] == "benchmark_validated_for_local_case_freeze"
    assert "finite-domain case-freeze" in task_text


def test_openfoam_c05_schema_rejects_wrong_solver() -> None:
    config = _config()
    config["solver"]["name"] = "simpleFoam"

    errors = list(Draft202012Validator(_schema()).iter_errors(config))

    assert errors
    assert any("pimpleFoam" in error.message for error in errors)
