from __future__ import annotations

from pathlib import Path

import pytest

from science_capability_registry.openfoam.evidence_contract import (
    build_runtime_artifacts,
    validate_evidence_manifest,
    write_validation_report,
)
from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.runner import (
    run as run_c01,
)


def test_openfoam_evidence_manifest_accepts_c01_dry_run(tmp_path: Path) -> None:
    manifest = run_c01(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=tmp_path / "c01",
        dry_run=True,
    )

    result = validate_evidence_manifest(manifest)

    assert result["capability_id"] == "cfd.openfoam.lid_driven_cavity_incompressible_laminar"
    assert result["validation"]["passed"] is True


def test_openfoam_evidence_manifest_accepts_runtime_branch(tmp_path: Path) -> None:
    manifest = run_c01(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=tmp_path / "c01_runtime_shape",
        dry_run=True,
    )
    manifest["backend"] = {"type": "wsl"}
    manifest["runtime"] = {
        "backend": "wsl",
        "wsl_distro": "Ubuntu-24.04",
        "bashrc_path": "/opt/OpenFOAM-v2112/etc/bashrc",
        "commands": [{"name": "icoFoam", "returncode": 0}],
        "metrics_json": str(tmp_path / "metrics.json"),
        "validation_json": str(tmp_path / "validation.json"),
    }

    result = validate_evidence_manifest(manifest)

    assert result["runtime"]["metrics_json"].endswith("metrics.json")


def test_openfoam_evidence_manifest_rejects_missing_runtime_metrics(tmp_path: Path) -> None:
    manifest = run_c01(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=tmp_path / "c01_bad_runtime",
        dry_run=True,
    )
    manifest["runtime"] = {
        "backend": "wsl",
        "commands": [{"name": "icoFoam", "returncode": 0}],
        "validation_json": str(tmp_path / "validation.json"),
    }

    with pytest.raises(ValueError, match="metrics_json"):
        validate_evidence_manifest(manifest)


def test_openfoam_evidence_manifest_rejects_missing_top_level_key(tmp_path: Path) -> None:
    manifest = run_c01(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=tmp_path / "c01_missing_key",
        dry_run=True,
    )
    del manifest["validation_targets"]

    with pytest.raises(ValueError, match="validation_targets"):
        validate_evidence_manifest(manifest)


def test_openfoam_runtime_artifacts_and_report_helpers(tmp_path: Path) -> None:
    artifacts = build_runtime_artifacts(
        tmp_path,
        logs={"solver": "log.icoFoam"},
        extra={"metrics": {"final_time_s": 0.5}},
    )
    report_path = tmp_path / "validation_report.md"
    write_validation_report(
        report_path,
        "OpenFOAM C01 Evidence Contract Smoke",
        {
            "passed": True,
            "gate": "smoke",
            "checks": [{"name": "manifest_envelope", "passed": True}],
        },
        ["Manifest envelope validates."],
        "shared evidence contract test",
    )

    assert str(tmp_path / "metrics.json") in artifacts["required_files"]
    report_text = report_path.read_text(encoding="utf-8")
    assert "OpenFOAM C01 Evidence Contract Smoke" in report_text
    assert "manifest_envelope: passed" in report_text
