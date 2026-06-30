from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation.runner import run


def test_openfoam_c02_runner_dry_run_writes_manifest_and_template_case() -> None:
    output_dir = Path("_results/openfoam/potential_flow_cylinder_analytical_validation/test_runner")
    result = run(
        config_path=Path("configs/openfoam/potential_flow_cylinder_analytical_validation/baseline.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/0/U").exists()
    assert (output_dir / "case/0/p").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    block_mesh = (output_dir / "case/system/blockMeshDict").read_text(encoding="utf-8")
    assert "type    coded" not in control
    assert "application     potentialFoam" in control
    assert "rInner  0.5;" in block_mesh
    assert "nRadial  10;" in block_mesh


def test_openfoam_c02_runner_dry_run_patches_mesh_refinement() -> None:
    output_dir = Path("_results/openfoam/potential_flow_cylinder_analytical_validation/test_runner_mesh_refined")
    result = run(
        config_path=Path("configs/openfoam/potential_flow_cylinder_analytical_validation/mesh_refined.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    block_mesh = (output_dir / "case/system/blockMeshDict").read_text(encoding="utf-8")
    assert "nRadial  20;" in block_mesh
    assert "nQuarter 20;" in block_mesh
    assert "nxOuter  40;" in block_mesh
    assert "nyOuter  40;" in block_mesh
