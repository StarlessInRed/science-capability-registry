from __future__ import annotations

import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.external_aero_force_coefficients.config import validate_case_config
from science_capability_registry.fluent.external_aero_force_coefficients.runner import run


def _write_fixture_zip(root: Path) -> None:
    package_dir = root / "Fluent_Tutorial_Package"
    package_dir.mkdir(parents=True)
    archive_path = package_dir / "fluent_aero_tutorial.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("fluent_aero_tutorial/IRT-Swept-Tail-Wing.cas.h5", "case")
        archive.writestr("fluent_aero_tutorial/oneram6-wing.msh.h5", "mesh")
        archive.writestr("fluent_aero_tutorial/Capsule_Input_3_Design_Points.csv", "DP,Mach Number\n1,0.3\n")
        archive.writestr(
            "fluent_aero_tutorial/reference_data/ref-onera-wing-Cl-vs-AoA.csv",
            "AoA [deg],Cl\n0,0.1\n2,0.2\n4,0.35\n",
        )
        archive.writestr(
            "fluent_aero_tutorial/reference_data/ref-onera-wing-Cp-7.5deg-section-z0.25m.csv",
            "x,Pressure Coefficient\n0.0,0.2\n0.5,-0.1\n",
        )
        archive.writestr(
            "fluent_aero_tutorial/reference_data/ref-irt-swept-wing-Cp-massflow-313-section-z0.6m.csv",
            "x,Pressure Coefficient\n0.0,0.3\n0.5,-0.2\n",
        )


def _fixture_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    result = deepcopy(config)
    for reference in result["reference_csvs"]:
        reference["min_rows"] = 2
    return validate_case_config(result)


def test_fluent_c04_runner_writes_reference_manifest(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["case_entry_count"] == 1
    assert result["metrics"]["mesh_entry_count"] == 1
    assert result["metrics"]["reference_csv_count"] == 3
    assert result["metrics"]["cl_curve_monotonic_non_decreasing"] is True
    for rel_path in [
        "aero_reference_manifest.json",
        "reference_tables.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]:
        assert (tmp_path / "out" / rel_path).exists()


def test_fluent_c04_runner_rejects_non_dry_run(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    try:
        run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=False)
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C04 non-dry-run rejection")
