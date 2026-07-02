from __future__ import annotations

import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.vof_free_surface_transient.config import validate_case_config
from science_capability_registry.fluent.vof_free_surface_transient.runner import run


def _write_fixture_zip(root: Path) -> None:
    package_dir = root / "Fluent_Tutorial_Package"
    package_dir.mkdir(parents=True)
    with zipfile.ZipFile(package_dir / "vof.zip", "w") as archive:
        archive.writestr("vof/inkjet.msh", "mesh")


def _fixture_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml").read_text(encoding="utf-8")
    )
    return validate_case_config(deepcopy(config))


def test_fluent_c05_runner_writes_mesh_setup_manifest(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["mesh_entry_count"] == 1
    assert result["metrics"]["solver_replay_status"] == "not_available_from_mesh_only_source"
    assert (tmp_path / "out" / "vof_setup_manifest.json").exists()


def test_fluent_c05_runner_rejects_non_dry_run(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    try:
        run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=False)
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C05 non-dry-run rejection")
