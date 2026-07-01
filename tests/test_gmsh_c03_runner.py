from __future__ import annotations

import csv
import json
from pathlib import Path

from science_capability_registry.gmsh.mesh_refinement_quality_trend.runner import run


def test_gmsh_c03_runner_dry_run_writes_refinement_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/mesh_refinement_quality_trend/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["element_count_monotonic"] is True
    for rel_path in [
        "refinement_matrix.csv",
        "mesh_quality_summary.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    rows = list(csv.DictReader((tmp_path / "refinement_matrix.csv").read_text(encoding="utf-8").splitlines()))
    summary = json.loads((tmp_path / "mesh_quality_summary.json").read_text(encoding="utf-8"))
    assert [row["level_id"] for row in rows] == ["coarse", "baseline", "fine"]
    assert summary["geometry_contract"]["boundary_contract_id"] == "meshing.gmsh.boundary_physical_group_contract"
    assert "does not claim that Gmsh has generated meshes" in (tmp_path / "validation_report.md").read_text(encoding="utf-8")
