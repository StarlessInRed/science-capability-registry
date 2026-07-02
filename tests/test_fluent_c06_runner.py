from __future__ import annotations

import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.sliding_rotating_mesh.config import validate_case_config
from science_capability_registry.fluent.sliding_rotating_mesh.runner import run


def _write_fixture_zips(root: Path) -> None:
    tutorial_dir = root / "Fluent_Tutorial_Package"
    legacy_dir = root / "legacy_2020_r2_unique"
    tutorial_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)
    with zipfile.ZipFile(tutorial_dir / "sliding_mesh.zip", "w") as archive:
        archive.writestr("sliding_mesh/axial_comp.msh", "mesh")
        archive.writestr("sliding_mesh/axial_comp.msh.h5", "mesh")
    with zipfile.ZipFile(legacy_dir / "single_rotating.zip", "w") as archive:
        archive.writestr("single_rotating/disk.msh", "mesh")


def _fixture_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    return validate_case_config(deepcopy(config))


def _fixture_runtime_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/sliding_rotating_mesh/sliding_mesh_axial_comp_mesh_read_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(deepcopy(config))


def test_fluent_c06_runner_writes_mesh_setup_manifest(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zips(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["source_package_count"] == 2
    assert result["metrics"]["mesh_entry_count"] == 3
    assert result["metrics"]["solver_replay_status"] == "not_available_from_mesh_only_sources"
    assert (tmp_path / "out" / "rotating_mesh_setup_manifest.json").exists()


def test_fluent_c06_runner_writes_mesh_read_smoke_journal(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zips(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_runtime_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is False
    assert (tmp_path / "out" / "axial_comp.msh").exists()
    journal_text = (tmp_path / "out" / "journal.jou").read_text(encoding="ascii")
    assert "/file/read-case" in journal_text
    assert "/mesh/check" in journal_text


def test_fluent_c06_runner_rejects_non_dry_run(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zips(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    try:
        run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=False)
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C06 non-dry-run rejection")
