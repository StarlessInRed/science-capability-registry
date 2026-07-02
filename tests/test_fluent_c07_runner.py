from __future__ import annotations

import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.heat_transfer_energy_balance.config import validate_case_config
from science_capability_registry.fluent.heat_transfer_energy_balance.runner import _heat_transfer_rates, run


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


def _fixture_runtime_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_read_smoke.yaml").read_text(
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


def test_fluent_c07_runner_writes_case_data_read_smoke_journal(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_runtime_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is False
    assert (tmp_path / "out" / "2d_heat_exchanger.cas.h5").exists()
    assert (tmp_path / "out" / "2d_heat_exchanger.dat.h5").exists()
    journal_text = (tmp_path / "out" / "journal.jou").read_text(encoding="ascii")
    assert "/file/read-case-data" in journal_text
    assert "/mesh/check" in journal_text
    assert "/report/volume-integrals/minimum" in journal_text
    assert "/report/volume-integrals/maximum" in journal_text
    assert journal_text.count("/report/surface-integrals/area-weighted-avg") == 2
    assert "/report/fluxes/heat-transfer" in journal_text


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


def test_fluent_c07_heat_transfer_parser_ignores_table_dividers() -> None:
    text = """
        Total Heat Transfer Rate                  [W]
-------------------------------- --------------------
                           inlet            285.10275
                          outlet           -1380.4602
                          wall-1            537.98133
                          wall-2            557.73616
                ---------------- --------------------
                             Net           0.36006308

> /exit yes
"""

    rates = _heat_transfer_rates(text)

    assert rates["Net"] == 0.36006308
    assert "----------------" not in rates
