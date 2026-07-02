from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.verification_reference_validation.config import validate_case_config
from science_capability_registry.fluent.verification_reference_validation.runner import run
from science_capability_registry.fluent.verification_reference_validation.validation import (
    summarize_mesh_runtime_metrics,
    validate_mesh_runtime_smoke,
    validate_reference_contract,
)


def _load_config() -> dict:
    data = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(data)


def test_fluent_c02_validation_accepts_formula_reference() -> None:
    validation = validate_reference_contract(_load_config())

    assert validation["passed"] is True
    assert any(item["name"] == "reference.formula_recomputes_target" and item["passed"] for item in validation["checks"])


def test_fluent_c02_validation_rejects_geometry_formula_mismatch() -> None:
    config = deepcopy(_load_config())
    config["reference_formula"]["pressure_drop_inputs"]["diameter_m"] = 0.003

    validation = validate_reference_contract(config)

    assert validation["passed"] is False
    assert any(item["name"] == "reference.formula_matches_geometry" and not item["passed"] for item in validation["checks"])


def test_fluent_c02_validation_accepts_mesh_runtime_metrics(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )
    config = validate_case_config(config)
    manifest = run(
        config=deepcopy(config),
        output_dir=tmp_path,
        dry_run=True,
    )
    runtime_metrics = {
        "fluent_return_code": 0,
        "mesh_node_count": 1377,
        "mesh_cell_count": 1280,
        "expected_mesh_cell_count": 1280,
        "mesh_face_counts": {
            "axis": 80,
            "interior": 2464,
            "pressure-outlet": 16,
            "velocity-inlet": 16,
            "wall": 80,
        },
        "mesh_check_completed": True,
        "minimum_cell_volume_m3": 9.765625e-8,
        "maximum_cell_volume_m3": 9.765625e-8,
        "total_cell_volume_m3": 1.25e-4,
        "fluent_warning_count": 2,
        "fluent_error_count": 0,
        "axis_boundary_warning_detected": True,
        "pressure_drop_runtime_status": "not_extracted_in_mesh_smoke",
        "runtime_scope": "mesh-readability and mesh/check only; no pressure-drop solve",
    }
    metrics = summarize_mesh_runtime_metrics(config, runtime_metrics)

    validation = validate_mesh_runtime_smoke(manifest, config, metrics, tmp_path, check_artifacts=False)

    assert validation["passed"] is True
    for rel_path in config["outputs"]["expected_outputs"]:
        assert rel_path in config["validation"]["required_artifacts"]
    assert any(item["name"] == "runtime.pressure_drop_not_claimed" and item["passed"] for item in validation["checks"])
