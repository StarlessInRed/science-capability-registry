from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.fluent.verification_reference_validation.runner import run


def test_fluent_c02_runner_writes_reference_manifest(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validated_config"] is True
    assert result["validation"]["passed"] is True
    assert result["metrics"]["manual_case_id"] == "VMFL005"
    assert abs(result["metrics"]["computed_formula_pressure_drop_pa"] - 10.24) < 1.0e-12
    assert result["metrics"]["manual_relative_error"] < 0.003
    for rel_path in [
        "reference_manifest.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    reference_manifest = json.loads((tmp_path / "reference_manifest.json").read_text(encoding="utf-8"))
    assert reference_manifest["reference_values"]["target_pressure_drop_pa"] == 10.24
    report_text = (tmp_path / "validation_report.md").read_text(encoding="utf-8")
    assert "VMFL005" in report_text
    assert "VMFL001" not in report_text


def test_fluent_c02_runner_rejects_non_dry_run(tmp_path: Path) -> None:
    try:
        run(
            config_path=Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml"),
            output_dir=tmp_path,
            dry_run=False,
        )
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C02 non-dry-run rejection")
