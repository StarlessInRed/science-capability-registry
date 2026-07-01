from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.gmsh.boundary_layer_size_field_meshing.runner import run


def test_gmsh_c05_runner_dry_run_writes_size_field_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/boundary_layer_size_field_meshing/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["near_wall_element_count"] == 32
    for rel_path in [
        "size_field_manifest.json",
        "boundary_layer_summary.json",
        "mesh_quality_summary.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    summary = json.loads((tmp_path / "boundary_layer_summary.json").read_text(encoding="utf-8"))
    assert summary["target_groups"] == ["wall"]
    assert "does not claim CFD y+ or downstream solver wall-function validity" in (
        tmp_path / "validation_report.md"
    ).read_text(encoding="utf-8")
