from __future__ import annotations

import json
from pathlib import Path

import pytest

from science_capability_registry.fluent.steady_internal_flow_runtime.runner import run


def test_fluent_c01_runner_dry_run_writes_journal_manifest(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validated_config"] is True
    assert result["validation"]["passed"] is True
    assert result["scope"] == "dry-run Fluent C01 journal contract"
    assert (tmp_path / "journal.jou").exists()
    assert (tmp_path / "manifest.json").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["fluent"]["dimension_precision"] == "2ddp"
    assert "/solve/iterate 1" in (tmp_path / "journal.jou").read_text(encoding="ascii")


def test_fluent_c01_runner_rejects_execution_without_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FLUENT_EXE", raising=False)
    monkeypatch.delenv("FLUENT_TUTORIAL_ROOT", raising=False)

    with pytest.raises(ValueError, match="FLUENT_TUTORIAL_ROOT"):
        run(
            config_path=Path("configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml"),
            output_dir=tmp_path,
            dry_run=False,
        )
