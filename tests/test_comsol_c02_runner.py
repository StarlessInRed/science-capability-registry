from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.comsol.model_construction_api_contract.runner import run

CONFIG_PATH = Path("configs/comsol/model_construction_api_contract/local_livelink_model_tree_smoke.yaml")


def test_comsol_c02_runner_dry_run_writes_script_manifest(tmp_path: Path) -> None:
    result = run(config_path=CONFIG_PATH, output_dir=tmp_path, dry_run=True)

    assert result["validated_config"] is True
    assert result["validation"]["passed"] is True
    assert result["scope"] == "COMSOL C02 dry-run model construction script contract; no MATLAB or COMSOL execution"
    assert (tmp_path / "matlab_model_construction_smoke.m").exists()
    assert (tmp_path / "manifest.json").exists()

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    script_text = (tmp_path / "matlab_model_construction_smoke.m").read_text(encoding="ascii")
    assert manifest["runtime_profile"] == "local_matlab_comsol_preflight"
    assert manifest["metrics"]["runtime_status"] == "dry_run_not_executed"
    assert "ModelUtil.create" in script_text
    assert "model.component.create" in script_text
    assert "model.component(componentTag).geom.create" in script_text
    assert "material.create" in script_text
    assert "mesh.create" in script_text
    assert "study.create" in script_text
    assert "mphevaluate" in script_text
    assert "mphrun" not in script_text
    assert ".run(studyTag)" not in script_text


def test_comsol_c02_runner_dry_run_does_not_require_runtime_manifests(tmp_path: Path) -> None:
    result = run(config_path=CONFIG_PATH, output_dir=tmp_path, dry_run=True)

    assert result["validation"]["passed"] is True
    assert not (tmp_path / "model_tree_manifest.json").exists()
    assert not (tmp_path / "construction_manifest.json").exists()
    assert result["metrics"]["solver_executed"] is False
