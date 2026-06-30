from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.runner import run


def test_openfoam_c08_runner_dry_run_writes_manifest_and_template_case() -> None:
    output_dir = Path("_results/openfoam/compressible_shock_capturing_forward_step/test_runner")
    result = run(
        config_path=Path("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/0/U").exists()
    assert (output_dir / "case/0/p").exists()
    assert (output_dir / "case/0/T").exists()
    assert not (output_dir / "case/0/rho").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "application     rhoCentralFoam" in control
    assert "maxCo           0.2;" in control
    assert "deltaT          0.002;" in control
    assert result["mesh_commands"] == ["blockMesh", "checkMesh"]
    assert result["solver_commands"] == ["blockMesh", "checkMesh", "rhoCentralFoam"]


def test_openfoam_c08_runner_dry_run_patches_reduced_cfl() -> None:
    output_dir = Path("_results/openfoam/compressible_shock_capturing_forward_step/test_runner_cfl")
    result = run(
        config_path=Path("configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "maxCo           0.1;" in control
    assert "deltaT          0.001;" in control
