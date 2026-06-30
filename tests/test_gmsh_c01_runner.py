from __future__ import annotations

from pathlib import Path

from science_capability_registry.gmsh.parametric_geometry_mesh_generation.runner import run


def test_gmsh_c01_runner_dry_run_writes_geo_and_manifest(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    geo_text = (tmp_path / "case.geo").read_text(encoding="utf-8")
    assert 'Physical Curve("inlet")' in geo_text
    assert 'Physical Curve("outlet")' in geo_text
    assert 'Physical Surface("fluid_domain")' in geo_text
    assert (tmp_path / "manifest.json").exists()
