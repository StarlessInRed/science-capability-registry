from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.runner import run


def test_openfoam_c04_runner_dry_run_writes_manifest_and_motorbike_case() -> None:
    output_dir = Path("_results/openfoam/external_aero_motorbike_rans_snappy/test_runner")
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/constant/triSurface/motorBike.obj.gz").exists()
    assert (output_dir / "case/0/U").exists()
    assert (output_dir / "case/system/snappyHexMeshDict").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert '#include "forceCoeffs"' in control
    assert "streamLines" not in control
    assert "no OpenFOAM solver execution" in result["scope"]


def test_openfoam_c04_runner_dry_run_plans_parallel_snappy_stages_in_order() -> None:
    output_dir = Path("_results/openfoam/external_aero_motorbike_rans_snappy/test_runner_sequence")
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    sequence_text = "\n".join(result["solver_commands"])
    assert "surfaceFeatureExtract" in sequence_text
    assert "mpirun -np 6 snappyHexMesh -overwrite -parallel" in sequence_text
    assert "for d in processor*" in sequence_text
    assert "mpirun -np 6 simpleFoam -parallel" in sequence_text
    assert "postProcess -latestTime -func yPlus" in sequence_text


def test_openfoam_c04_runner_dry_run_patches_force_coefficients_and_inlet_speed() -> None:
    output_dir = Path("_results/openfoam/external_aero_motorbike_rans_snappy/test_runner_speed")
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/inlet_speed_scaled.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    initial = (output_dir / "case/0/include/initialConditions").read_text(encoding="utf-8")
    force = (output_dir / "case/system/forceCoeffs").read_text(encoding="utf-8")
    assert "flowVelocity         (25 0 0);" in initial
    assert "magUInf         25;" in force
    assert "Aref            0.75;" in force
