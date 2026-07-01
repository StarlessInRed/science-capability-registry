from __future__ import annotations

import csv
import json
from pathlib import Path

from science_capability_registry.gmsh.multi_solver_mesh_export_contract.runner import run


def test_gmsh_c06_runner_dry_run_writes_export_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/multi_solver_mesh_export_contract/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["solver_family_count"] == 2
    for rel_path in [
        "export_manifest.json",
        "format_matrix.csv",
        "solver_import_summary.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    rows = list(csv.DictReader((tmp_path / "format_matrix.csv").read_text(encoding="utf-8").splitlines()))
    import_summary = json.loads((tmp_path / "solver_import_summary.json").read_text(encoding="utf-8"))
    assert {row["target_id"] for row in rows} == {"openfoam_gmshToFoam", "fenicsx_xdmf"}
    assert import_summary["status"] == "static_contract_only"
    assert "does not claim that any downstream solver import command has been executed" in (
        tmp_path / "validation_report.md"
    ).read_text(encoding="utf-8")
