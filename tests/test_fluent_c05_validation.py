from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.vof_free_surface_transient.config import validate_case_config
from science_capability_registry.fluent.vof_free_surface_transient.validation import (
    summarize_metrics,
    validate_manifest,
)


def _load_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    return validate_case_config(config)


def _manifest() -> dict:
    return {
        "capability_id": "cfd.fluent.vof_free_surface_transient",
        "case_id": "vof_inkjet_mesh_setup_static",
        "archive": {
            "archive_status": "readable",
            "error_message": "",
            "entry_count": 1,
            "entry_kind_counts": {"mesh": 1},
        },
        "mesh_entries": [{"entry_path": "vof/inkjet.msh", "entry_kind": "mesh", "compound_extension": ".msh", "size": 10}],
        "mesh_format_counts": {".msh": 1},
        "generated_files": [
            "vof_setup_manifest.json",
            "mesh_entries.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ],
    }


def test_fluent_c05_validation_accepts_mesh_only_manifest() -> None:
    config = _load_config()
    manifest = _manifest()
    validation = validate_manifest(manifest, config)
    metrics = summarize_metrics(manifest, validation)

    assert validation["passed"] is True
    assert metrics["mesh_entry_count"] == 1


def test_fluent_c05_validation_rejects_case_data_claim_in_mesh_only_source() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["archive"]["entry_kind_counts"]["case"] = 1

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "source.mesh_only_boundary" and not item["passed"] for item in validation["checks"])
