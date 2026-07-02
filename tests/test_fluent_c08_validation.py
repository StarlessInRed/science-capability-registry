from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.workbench_parameter_integration.config import validate_case_config
from science_capability_registry.fluent.workbench_parameter_integration.validation import (
    summarize_metrics,
    validate_manifest,
)


def _load_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(config)


def _manifest() -> dict:
    return {
        "capability_id": "cfd.fluent.workbench_parameter_integration",
        "case_id": "workbench_parameter_wbpz_static",
        "outer_archive": {
            "archive_status": "readable",
            "error_message": "",
            "entry_kind_counts": {"workbench_archive": 1},
        },
        "nested_archive": {
            "archive_status": "readable",
            "error_message": "",
            "entry_count": 6,
            "entry_kind_counts": {
                "workbench_project_file": 1,
                "design_point_file": 1,
                "workbench_journal": 1,
                "design_point_log": 1,
                "geometry_database": 1,
                "mesh_database": 1,
            },
        },
        "workbench_project": {
            "external_version_string": "2020 R2",
            "framework_build_version": "20.2.210.0",
            "last_saved_utc": "05/11/2020 18:58:06",
            "project_version": "9.1",
        },
        "current_parameters": [
            {"parameter_name": "P1", "display_text": "hcpos", "expression": "90", "usage": "Input", "value": "90", "quantity_name": "Dimensionless"},
            {"parameter_name": "P2", "display_text": "ftpos", "expression": "25", "usage": "Input", "value": "25", "quantity_name": "Dimensionless"},
            {"parameter_name": "P3", "display_text": "wsfpos", "expression": "175", "usage": "Input", "value": "175", "quantity_name": "Dimensionless"},
        ],
        "design_point_log": {"headers": ["Name", "P1", "P2", "P3"], "data_row_count": 1, "sample_rows": [["DP 0", "90", "25", "175"]]},
        "runwb2_preflight": {
            "static_gate_requires_runwb2": False,
            "runwb2_executable": {"configured": False},
            "fluent_executable": {"configured": False},
            "ansys_root": {"configured": False},
        },
        "generated_files": [
            "workbench_project_manifest.json",
            "workbench_entries.json",
            "parameter_table.csv",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ],
    }


def test_fluent_c08_validation_accepts_workbench_manifest() -> None:
    config = _load_config()
    manifest = _manifest()
    validation = validate_manifest(manifest, config)
    metrics = summarize_metrics(manifest, validation)

    assert validation["passed"] is True
    assert metrics["current_parameter_count"] == 3


def test_fluent_c08_validation_rejects_missing_workbench_project_file() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["nested_archive"]["entry_kind_counts"].pop("workbench_project_file")

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "nested.entry_class.workbench_project_file" and not item["passed"] for item in validation["checks"])
