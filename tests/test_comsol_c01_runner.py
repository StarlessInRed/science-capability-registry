from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.comsol.matlab_server_bridge_runtime.config import validate_case_config
from science_capability_registry.comsol.matlab_server_bridge_runtime.runner import run

CONFIG_PATH = Path("configs/comsol/matlab_server_bridge_runtime/local_preflight.yaml")


def _config() -> dict:
    return validate_case_config(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")))


def test_comsol_c01_runner_dry_run_writes_script_manifest(tmp_path: Path) -> None:
    result = run(config_path=CONFIG_PATH, output_dir=tmp_path, dry_run=True)

    assert result["validated_config"] is True
    assert result["validation"]["passed"] is True
    assert result["scope"] == "COMSOL C01 dry-run script contract; no MATLAB or COMSOL execution"
    assert (tmp_path / "matlab_bridge_smoke.m").exists()
    assert (tmp_path / "manifest.json").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    script_text = (tmp_path / "matlab_bridge_smoke.m").read_text(encoding="ascii")
    assert manifest["runtime_profile"] == "local_matlab_comsol_preflight"
    assert "ModelUtil.create" in script_text
    assert "COMSOL_MLI_DIR" in script_text


def test_comsol_c01_preflight_records_missing_environment(monkeypatch, tmp_path: Path) -> None:
    for name in ["MATLAB_EXE", "COMSOL_BIN", "COMSOL_MLI_DIR", "COMSOL_MPHSERVER_BIN"]:
        monkeypatch.delenv(name, raising=False)

    result = run(config_path=CONFIG_PATH, output_dir=tmp_path, dry_run=False)

    assert result["validation"]["passed"] is False
    assert result["metrics"]["environment_summary"]["required_configured_count"] == 0
    assert result["metrics"]["runtime_status"] == "blocked_by_runtime_profile"


def test_comsol_c01_preflight_passes_with_fake_existing_env(monkeypatch, tmp_path: Path) -> None:
    matlab_exe = tmp_path / "matlab.exe"
    comsol_bin = tmp_path / "comsol.exe"
    livelink_dir = tmp_path / "mli"
    matlab_exe.write_text("fixture", encoding="ascii")
    comsol_bin.write_text("fixture", encoding="ascii")
    livelink_dir.mkdir()
    monkeypatch.setenv("MATLAB_EXE", str(matlab_exe))
    monkeypatch.setenv("COMSOL_BIN", str(comsol_bin))
    monkeypatch.setenv("COMSOL_MLI_DIR", str(livelink_dir))

    config = deepcopy(_config())
    config["backend"]["type"] = "preflight_only"
    result = run(config=config, output_dir=tmp_path / "out", dry_run=False)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["environment_summary"]["required_existing_count"] == 3
    assert result["metrics"]["matlab_executed"] is False
