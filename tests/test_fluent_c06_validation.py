from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.sliding_rotating_mesh.config import validate_case_config
from science_capability_registry.fluent.sliding_rotating_mesh.validation import (
    summarize_metrics,
    validate_manifest,
)


def _load_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    return validate_case_config(config)


def _manifest() -> dict:
    return {
        "capability_id": "cfd.fluent.sliding_rotating_mesh",
        "case_id": "sliding_rotating_mesh_setup_static",
        "packages": [
            {
                "source_id": "C06_sliding_mesh",
                "archive_status": "readable",
                "entry_kind_counts": {"mesh": 2},
            },
            {
                "source_id": "C06_single_rotating_legacy",
                "archive_status": "readable",
                "entry_kind_counts": {"mesh": 1},
            },
        ],
        "mesh_entries": [
            {"entry_path": "sliding_mesh/axial_comp.msh", "entry_kind": "mesh", "compound_extension": ".msh", "size": 10},
            {"entry_path": "sliding_mesh/axial_comp.msh.h5", "entry_kind": "mesh", "compound_extension": ".msh.h5", "size": 20},
            {"entry_path": "single_rotating/disk.msh", "entry_kind": "mesh", "compound_extension": ".msh", "size": 30},
        ],
        "mesh_format_counts": {".msh": 2, ".msh.h5": 1},
        "generated_files": [
            "rotating_mesh_setup_manifest.json",
            "mesh_entries.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ],
    }


def test_fluent_c06_validation_accepts_mesh_only_sources() -> None:
    config = _load_config()
    manifest = _manifest()
    validation = validate_manifest(manifest, config)
    metrics = summarize_metrics(manifest, validation)

    assert validation["passed"] is True
    assert metrics["mesh_entry_count"] == 3


def test_fluent_c06_validation_rejects_missing_required_source() -> None:
    config = _load_config()
    manifest = deepcopy(_manifest())
    manifest["packages"] = manifest["packages"][:1]

    validation = validate_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "sources.required_source_ids" and not item["passed"] for item in validation["checks"])
