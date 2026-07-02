from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(".")
MAP_PATH = ROOT / "software" / "comsol" / "capability_map.md"
INDEX_PATH = ROOT / "software" / "comsol" / "examples_index.md"
EVIDENCE_INDEX_PATH = ROOT / "reports" / "evidence_index.yaml"
CARD_SCHEMA_PATH = ROOT / "schemas" / "capability_card.schema.json"

COMSOL_ASSETS = {
    "C01": "software/comsol/assets/C01_matlab_server_bridge_runtime.yaml",
    "C02": "software/comsol/assets/C02_model_construction_api_contract.yaml",
    "C03": "software/comsol/assets/C03_geometry_mesh_import_contract.yaml",
    "C04": "software/comsol/assets/C04_physics_boundary_assignment_contract.yaml",
    "C05": "software/comsol/assets/C05_study_run_solver_smoke.yaml",
    "C06": "software/comsol/assets/C06_result_extraction_postprocess_validation.yaml",
}

COMSOL_TASKS = {
    "C01": "tasks/comsol_C01_matlab_server_bridge_runtime_intern_task.md",
    "C02": "tasks/comsol_C02_model_construction_api_contract_intern_task.md",
    "C03": "tasks/comsol_C03_geometry_mesh_import_contract_intern_task.md",
    "C04": "tasks/comsol_C04_physics_boundary_assignment_contract_intern_task.md",
    "C05": "tasks/comsol_C05_study_run_solver_smoke_intern_task.md",
    "C06": "tasks/comsol_C06_result_extraction_postprocess_validation_intern_task.md",
}

COMSOL_EVIDENCE_ID = "comsol_C01_C06_matlab_driver_capability_map_2026-07-02"
COMSOL_C03_C06_CANDIDATE_EVIDENCE_ID = "comsol_C03_C06_application_library_replay_candidates_2026-07-03"
COMSOL_C03_C06_NEGATIVE_EVIDENCE_ID = "comsol_C03_C06_negative_validation_2026-07-03"
CANDIDATE_CONFIG_PATH = ROOT / "configs" / "comsol" / "application_library_replay_candidates" / "c03_c06_official_candidates.yaml"


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _card_schema() -> dict[str, Any]:
    return json.loads(CARD_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_comsol_c01_c06_capability_map_links_assets_and_tasks() -> None:
    map_text = MAP_PATH.read_text(encoding="utf-8")
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    validator = Draft202012Validator(_card_schema())

    for c_id, asset_path in COMSOL_ASSETS.items():
        asset = _read_yaml(ROOT / asset_path)
        errors = sorted(
            validator.iter_errors(asset), key=lambda error: list(error.path)
        )

        assert not errors, [error.message for error in errors]
        assert asset["software"] == "COMSOL"
        assert asset["domain"] == "multiphysics"
        assert asset["card_status"] == "review"
        assert asset["benchmark_status"] == "package_skeleton_created"
        assert asset_path in index_text
        assert c_id in map_text

    for task_path in COMSOL_TASKS.values():
        task_text = (ROOT / task_path).read_text(encoding="utf-8")
        assert "## 验证标准" in task_text


def test_comsol_capability_map_evidence_entry_resolves() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }
    evidence = evidence_by_id[COMSOL_EVIDENCE_ID]

    assert evidence["asset_path"] == MAP_PATH.as_posix()
    assert evidence["gate"] == "static-readiness"
    assert evidence["status"] == "indexed"
    assert evidence["runtime_evidence_paths"] == []
    assert Path(evidence["primary_evidence_path"]).exists()

    for path in evidence["supporting_paths"]:
        assert Path(path).exists(), path


def test_comsol_c01_package_skeleton_evidence_entry_resolves() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }
    evidence = evidence_by_id[
        "comsol_C01_matlab_server_bridge_runtime_preflight_skeleton_2026-07-03"
    ]

    assert evidence["asset_path"] == COMSOL_ASSETS["C01"]
    assert evidence["gate"] == "static-readiness"
    assert evidence["status"] == "indexed"
    assert evidence["runtime_evidence_paths"] == []
    assert Path(evidence["primary_evidence_path"]).exists()
    for path in evidence["supporting_paths"]:
        assert Path(path).exists(), path


def test_comsol_c01_livelink_smoke_evidence_entry_resolves() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }
    evidence = evidence_by_id[
        "comsol_C01_matlab_server_bridge_runtime_livelink_smoke_2026-07-03"
    ]

    assert evidence["asset_path"] == COMSOL_ASSETS["C01"]
    assert evidence["gate"] == "smoke"
    assert evidence["status"] == "passed"
    assert evidence["runtime_evidence_paths"] == [
        "_results/comsol/matlab_server_bridge_runtime/local_livelink_smoke/"
    ]
    assert Path(evidence["primary_evidence_path"]).exists()
    for path in evidence["supporting_paths"]:
        assert Path(path).exists(), path


def test_comsol_c02_c06_package_evidence_entries_resolve() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }
    expected = {
        "comsol_C02_model_construction_api_contract_livelink_smoke_2026-07-03": (
            "C02",
            "smoke",
            "passed",
        ),
        "comsol_C03_geometry_mesh_import_contract_static_skeleton_2026-07-03": (
            "C03",
            "static-readiness",
            "passed",
        ),
        "comsol_C03_geometry_mesh_import_contract_livelink_heat_rectangle_smoke_2026-07-03": (
            "C03",
            "smoke",
            "passed",
        ),
        "comsol_C04_physics_boundary_assignment_contract_static_skeleton_2026-07-03": (
            "C04",
            "static-readiness",
            "passed",
        ),
        "comsol_C04_physics_boundary_assignment_contract_livelink_heat_rectangle_smoke_2026-07-03": (
            "C04",
            "smoke",
            "passed",
        ),
        "comsol_C05_study_run_solver_smoke_static_skeleton_2026-07-03": (
            "C05",
            "static-readiness",
            "passed",
        ),
        "comsol_C05_study_run_solver_smoke_livelink_heat_rectangle_smoke_2026-07-03": (
            "C05",
            "smoke",
            "passed",
        ),
        "comsol_C06_result_extraction_postprocess_validation_static_skeleton_2026-07-03": (
            "C06",
            "static-readiness",
            "passed",
        ),
        "comsol_C06_result_extraction_postprocess_validation_livelink_heat_rectangle_smoke_2026-07-03": (
            "C06",
            "smoke",
            "passed",
        ),
    }

    for evidence_id, (c_id, gate, status) in expected.items():
        evidence = evidence_by_id[evidence_id]
        assert evidence["asset_path"] == COMSOL_ASSETS[c_id]
        assert evidence["gate"] == gate
        assert evidence["status"] == status
        if gate == "smoke":
            assert evidence["runtime_evidence_paths"]
            assert evidence["evidence_kind"] == "runtime_smoke_report"
        assert Path(evidence["primary_evidence_path"]).exists()
        for path in evidence["supporting_paths"]:
            assert Path(path).exists(), path


def test_comsol_runtime_smoke_does_not_claim_benchmark_validation() -> None:
    report_text = Path(
        "reports/comsol_C01_C06_matlab_driver_capability_map_2026-07-02.md"
    ).read_text(encoding="utf-8")
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    map_text = MAP_PATH.read_text(encoding="utf-8")

    assert "No MATLAB/COMSOL runtime execution is claimed" in report_text
    assert "benchmark validation" in index_text
    assert "benchmark validation" in map_text


def test_comsol_c03_c06_candidate_config_preserves_env_root_boundary() -> None:
    config = _read_yaml(CANDIDATE_CONFIG_PATH)
    serialized = yaml.safe_dump(config, sort_keys=True)

    assert config["selection_status"] == "candidate_selected_not_executed"
    assert config["root_policy"]["application_library_root_env"] == "COMSOL_APPLICATION_LIBRARY_ROOT"
    assert config["root_policy"]["committed_absolute_paths"] is False
    assert config["primary_replay_candidates"][0]["candidate_id"] == "livelink_domain_activation"
    assert config["primary_replay_candidates"][1]["candidate_id"] == "livelink_pseudoperiodicity"
    for drive_letter in "CDEFG":
        assert f"{drive_letter}:{chr(92)}" not in serialized
    assert "official replay runner has executed" in "\n".join(config["not_validated_yet"])
    assert "benchmark validation is claimed" in "\n".join(config["not_validated_yet"])


def test_comsol_c03_c06_candidate_and_negative_evidence_entries_resolve() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }

    candidate = evidence_by_id[COMSOL_C03_C06_CANDIDATE_EVIDENCE_ID]
    assert candidate["asset_path"] == MAP_PATH.as_posix()
    assert candidate["gate"] == "static-readiness"
    assert candidate["status"] == "indexed"
    assert candidate["runtime_evidence_paths"] == []
    assert "official .mph replay" in "\n".join(candidate["limitations"])

    negative = evidence_by_id[COMSOL_C03_C06_NEGATIVE_EVIDENCE_ID]
    assert negative["asset_path"] == MAP_PATH.as_posix()
    assert negative["gate"] == "targeted-regression"
    assert negative["status"] == "passed"
    assert negative["runtime_evidence_paths"] == []
    assert "Failure-localization tests only" in "\n".join(negative["limitations"])

    for evidence in (candidate, negative):
        assert Path(evidence["primary_evidence_path"]).exists()
        for path in evidence["supporting_paths"]:
            assert Path(path).exists(), path
