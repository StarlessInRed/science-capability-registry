from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.heat_transfer_energy_balance.config import validate_case_config
from science_capability_registry.fluent.heat_transfer_energy_balance.validation import (
    summarize_metrics,
    validate_manifest,
)


def _load_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(config)


def _load_runtime_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_read_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(config)


def _manifest() -> dict:
    return {
        "capability_id": "cfd.fluent.heat_transfer_energy_balance",
        "case_id": "heat_exchanger_case_data_static",
        "archive": {
            "archive_status": "readable",
            "error_message": "",
            "entry_count": 2,
            "entry_kind_counts": {"case": 1, "data": 1},
        },
        "entries": [
            {"entry_path": "case.cas.h5", "entry_kind": "case", "size": 10},
            {"entry_path": "case.dat.h5", "entry_kind": "data", "size": 20},
        ],
        "case_data_pairs": [{"pair_id": "case", "case_entry": "case.cas.h5", "data_entry": "case.dat.h5"}],
        "generated_files": [
            "heat_transfer_source_manifest.json",
            "case_data_entries.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ],
    }


def test_fluent_c07_validation_accepts_case_data_pair() -> None:
    config = _load_config()
    manifest = _manifest()
    validation = validate_manifest(manifest, config)
    metrics = summarize_metrics(manifest, validation)

    assert validation["passed"] is True
    assert metrics["case_data_pair_count"] == 1


def test_fluent_c07_validation_rejects_missing_data_pair() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["case_data_pairs"] = []

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "source.case_data_pair_count" and not item["passed"] for item in validation["checks"])


def test_fluent_c07_validation_accepts_thermal_report_smoke_metrics() -> None:
    config = _load_runtime_config()
    manifest = deepcopy(_manifest())
    manifest["case_id"] = "heat_exchanger_case_data_read_smoke"
    manifest["generated_files"] = [
        "heat_transfer_source_manifest.json",
        "case_data_entries.json",
        "2d_heat_exchanger.cas.h5",
        "2d_heat_exchanger.dat.h5",
        "journal.jou",
        "stdout.txt",
        "stderr.txt",
        "transcript.txt",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    manifest["runtime_metrics"] = {
        "fluent_return_code": 0,
        "mesh_cell_count": 1200,
        "mesh_check_completed": True,
        "fluent_warning_count": 0,
        "fluent_error_count": 0,
        "temperature_min_k": 299.99997,
        "temperature_max_k": 494.50212,
        "surface_area_weighted_temperature_k": {"inlet": 300.0, "outlet": 307.49261},
        "heat_transfer_rates_w": {
            "inlet": 285.10275,
            "outlet": -1380.4602,
            "wall-1": 537.98133,
            "wall-2": 557.73616,
            "Net": 0.36006308,
        },
        "heat_transfer_net_w": 0.36006308,
        "heat_transfer_balance_relative_error": 0.00013039416416868554,
    }

    validation = validate_manifest(manifest, config)
    metrics = summarize_metrics(manifest, validation)

    assert validation["passed"] is True
    assert metrics["temperature_min_k"] == 299.99997
    assert any(item["name"] == "runtime.heat_transfer_balance_error" and item["passed"] for item in validation["checks"])
