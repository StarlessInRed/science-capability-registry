from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.gmsh.cad_import_geometry_healing.runner import run


def test_gmsh_c04_runner_dry_run_writes_cad_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/cad_import_geometry_healing/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["imported_surface_count"] == 1
    for rel_path in [
        "cad_import_manifest.json",
        "entity_map.json",
        "healing_report.json",
        "meshability_summary.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    manifest = json.loads((tmp_path / "cad_import_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cad_source"]["source_kind"] == "generated_smoke"
    assert "does not claim that OpenCASCADE import has executed" in (
        tmp_path / "validation_report.md"
    ).read_text(encoding="utf-8")
