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
