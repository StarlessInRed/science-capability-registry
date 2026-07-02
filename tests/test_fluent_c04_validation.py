from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.external_aero_force_coefficients.config import validate_case_config
from science_capability_registry.fluent.external_aero_force_coefficients.validation import (
    summarize_metrics,
    validate_manifest,
)


def _load_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(config)


def _manifest() -> dict:
    return {
        "capability_id": "cfd.fluent.external_aero_force_coefficients",
        "case_id": "fluent_aero_reference_csv_static",
        "archive": {
            "archive_status": "readable",
            "error_message": "",
            "entry_count": 6,
            "entry_kind_counts": {
                "case": 1,
                "mesh": 1,
                "reference_csv": 3,
                "design_or_table_csv": 1,
            },
        },
        "reference_tables": [
            {
                "reference_id": "onera_cl_vs_aoa",
                "reference_role": "lift_curve",
                "entry_path": "ref.csv",
                "columns": ["AoA [deg]", "Cl"],
                "required_columns": ["AoA [deg]", "Cl"],
                "row_count": 7,
                "finite_numeric_values": 14,
                "nonfinite_cells": [],
                "numeric_ranges": {"Cl": {"min": 0.1, "max": 0.6}},
                "trend_checks": {
                    "aoa_monotonic_non_decreasing": True,
                    "cl_monotonic_non_decreasing": True,
                    "cl_min": 0.1,
                    "cl_max": 0.6,
                },
            },
            {
                "reference_id": "onera_cp_7p5deg_section_z0p25m",
                "reference_role": "pressure_coefficient_section",
                "entry_path": "ref.csv",
                "columns": ["x", "Pressure Coefficient"],
                "required_columns": ["x", "Pressure Coefficient"],
                "row_count": 10,
                "finite_numeric_values": 20,
                "nonfinite_cells": [],
                "numeric_ranges": {"Pressure Coefficient": {"min": -1.0, "max": 0.5}},
                "trend_checks": {},
            },
            {
                "reference_id": "irt_swept_wing_cp_massflow_313_section_z0p6m",
                "reference_role": "pressure_coefficient_section",
                "entry_path": "ref.csv",
                "columns": ["x", "Pressure Coefficient"],
                "required_columns": ["x", "Pressure Coefficient"],
                "row_count": 10,
                "finite_numeric_values": 20,
                "nonfinite_cells": [],
                "numeric_ranges": {"Pressure Coefficient": {"min": -1.0, "max": 0.5}},
                "trend_checks": {},
            },
        ],
        "generated_files": [
            "aero_reference_manifest.json",
            "reference_tables.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ],
    }


def test_fluent_c04_validation_accepts_reference_manifest() -> None:
    config = _load_config()
    validation = validate_manifest(_manifest(), config)
    metrics = summarize_metrics(_manifest(), validation)

    assert validation["passed"] is True
    assert metrics["reference_table_count"] == 3
    assert metrics["cl_curve_monotonic_non_decreasing"] is True


def test_fluent_c04_validation_rejects_broken_lift_curve_trend() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["reference_tables"][0]["trend_checks"]["cl_monotonic_non_decreasing"] = False

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "physics.lift_curve_trend" and not item["passed"] for item in validation["checks"])


def test_fluent_c04_validation_rejects_missing_required_reference_role() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["reference_tables"] = [
        table for table in manifest["reference_tables"] if table["reference_role"] != "pressure_coefficient_section"
    ]

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(
        item["name"] == "reference.role.pressure_coefficient_section" and not item["passed"]
        for item in validation["checks"]
    )
