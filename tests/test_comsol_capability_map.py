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
        errors = sorted(validator.iter_errors(asset), key=lambda error: list(error.path))

        assert not errors, [error.message for error in errors]
        assert asset["software"] == "COMSOL"
        assert asset["domain"] == "multiphysics"
        assert asset["card_status"] == "review"
        assert asset["benchmark_status"] == "benchmark_candidate"
        assert asset_path in index_text
        assert c_id in map_text

    for task_path in COMSOL_TASKS.values():
        task_text = (ROOT / task_path).read_text(encoding="utf-8")
        assert "## 验证标准" in task_text


def test_comsol_capability_map_evidence_entry_resolves() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {entry["evidence_id"]: entry for entry in evidence_index["evidence"]}
    evidence = evidence_by_id[COMSOL_EVIDENCE_ID]

    assert evidence["asset_path"] == MAP_PATH.as_posix()
    assert evidence["gate"] == "static-readiness"
    assert evidence["status"] == "indexed"
    assert evidence["runtime_evidence_paths"] == []
    assert Path(evidence["primary_evidence_path"]).exists()

    for path in evidence["supporting_paths"]:
        assert Path(path).exists(), path


def test_comsol_first_gate_does_not_claim_runtime() -> None:
    report_text = Path("reports/comsol_C01_C06_matlab_driver_capability_map_2026-07-02.md").read_text(
        encoding="utf-8"
    )
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "No MATLAB/COMSOL runtime execution is claimed" in report_text
    assert "Do not claim COMSOL runtime without a recorded MATLAB/COMSOL executable profile" in index_text
