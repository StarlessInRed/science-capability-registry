from __future__ import annotations

import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.heat_transfer_energy_balance.config import validate_case_config
from science_capability_registry.fluent.heat_transfer_energy_balance.runner import run


def _write_fixture_zip(root: Path) -> None:
    package_dir = root / "Fluent_Tutorial_Package"
    package_dir.mkdir(parents=True)
    with zipfile.ZipFile(package_dir / "2d_heat_exchanger_optimizer.zip", "w") as archive:
        archive.writestr("2d_heat_exchanger_optimizer/2d_heat_exchanger.cas.h5", "case")
        archive.writestr("2d_heat_exchanger_optimizer/2d_heat_exchanger.dat.h5", "data")


def _fixture_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(deepcopy(config))


def test_fluent_c07_runner_writes_case_data_manifest(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["case_entry_count"] == 1
    assert result["metrics"]["data_entry_count"] == 1
    assert result["metrics"]["case_data_pair_count"] == 1
    assert (tmp_path / "out" / "heat_transfer_source_manifest.json").exists()


def test_fluent_c07_runner_rejects_non_dry_run(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    try:
        run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=False)
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C07 non-dry-run rejection")
