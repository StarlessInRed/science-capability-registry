from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.comsol.geometry_mesh_import_contract import run as run_c03
from science_capability_registry.comsol.static_contract import REPO_ROOT, validate_static_manifest

C03_CONFIG = Path("configs/comsol/geometry_mesh_import_contract/static_contract.yaml")
C03_SCHEMA = REPO_ROOT / "schemas/comsol_C03_geometry_mesh_import_contract.schema.json"


def test_comsol_static_validation_rejects_missing_required_role() -> None:
    config = yaml.safe_load(C03_CONFIG.read_text(encoding="utf-8"))
    config["contract"]["declared_objects"] = [
        item for item in config["contract"]["declared_objects"] if item["role"] != "selection_map"
    ]
    manifest = {
        "validated_config": True,
        "runtime_executed": False,
        "backend": config["backend"],
        "contract": config["contract"],
        "generated_files": config["outputs"]["expected_outputs"],
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
    }

    validation = validate_static_manifest(manifest, config)

    assert validation["passed"] is False
    assert any(item["name"] == "object_role.present.selection_map" and not item["passed"] for item in validation["checks"])


def test_comsol_static_runner_rejects_non_dry_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="dry_run only"):
        run_c03(config_path=C03_CONFIG, output_dir=tmp_path, dry_run=False)
