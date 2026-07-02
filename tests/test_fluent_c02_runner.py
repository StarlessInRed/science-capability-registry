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


def test_fluent_c02_runner_writes_self_generated_mesh_contract(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validated_config"] is True
    assert result["mesh_generation"]["axial_cells"] == 80
    mesh_text = (tmp_path / "pipe_axisymmetric_mesh.msh").read_text(encoding="ascii")
    journal_text = (tmp_path / "journal.jou").read_text(encoding="ascii")
    mesh_manifest = json.loads((tmp_path / "mesh_manifest.json").read_text(encoding="utf-8"))

    assert "(45 (4 axis axis)())" in mesh_text
    assert "/file/read-case" in journal_text
    assert "/mesh/check" in journal_text
    assert mesh_manifest["cell_count"] == 80 * 16
    assert mesh_manifest["axis_face_zone_type"] == "axis"


def test_fluent_c02_runner_writes_pressure_solve_journal_contract(tmp_path: Path) -> None:
    result = run(
        config_path=Path(
            "configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_pressure_solve_smoke.yaml"
        ),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validated_config"] is True
    assert result["solver_setup"]["model_state"] == "axisymmetric"
    journal_text = (tmp_path / "journal.jou").read_text(encoding="ascii")

    assert "/define/models/axisymmetric yes" in journal_text
    assert "/define/models/viscous/laminar yes" in journal_text
    assert "/define/materials/change-create air air" in journal_text
    assert "/define/boundary-conditions/velocity-inlet inlet" in journal_text
    assert "/solve/initialize/hyb-initialization" in journal_text
    assert "/solve/iterate 50" in journal_text
    assert journal_text.count("/report/surface-integrals/area-weighted-avg") == 2
    assert "pressure\nno" in journal_text


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
