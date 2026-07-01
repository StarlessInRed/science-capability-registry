from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy import cli
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


def test_openfoam_c04_runner_solver_only_dry_run_omits_force_functions(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_solver_only_wsl_v2112.yaml"),
        output_dir=tmp_path,
        dry_run=True,
        backend="dry_run_only",
    )

    assert result["validation"]["passed"] is True
    assert result["postprocess_commands"] == []
    control = (tmp_path / "case/system/controlDict").read_text(encoding="utf-8")
    assert "functions\n{}" in control
    assert '#include "forceCoeffs"' not in control


def test_openfoam_c04_runner_applies_snappy_config_to_dictionary(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_solver_only_wsl_v2112.yaml"),
        output_dir=tmp_path,
        dry_run=True,
        backend="dry_run_only",
    )

    assert result["validation"]["passed"] is True
    snappy = (tmp_path / "case/system/snappyHexMeshDict").read_text(encoding="utf-8")
    assert "castellatedMesh true;" in snappy
    assert "snap            true;" in snappy
    assert "addLayers       false;" in snappy
    assert "level (5 6);" in snappy
    assert "level 6;" in snappy
    assert "levels ((1E15 4));" in snappy
    assert "nSurfaceLayers 0;" in snappy
    quality = (tmp_path / "case/system/meshQualityDict").read_text(encoding="utf-8")
    assert "\nminFaceWeight 0.02;" in quality


def test_openfoam_c04_runner_applies_snap_controls_to_dictionary(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_snap_probe_layer0_wsl_v2112.yaml"),
        output_dir=tmp_path,
        dry_run=True,
        backend="dry_run_only",
    )

    assert result["validation"]["passed"] is True
    snappy = (tmp_path / "case/system/snappyHexMeshDict").read_text(encoding="utf-8")
    assert "nSmoothPatch 5;" in snappy
    assert "tolerance 4;" in snappy
    assert "nSolveIter 100;" in snappy
    assert "nRelaxIter 8;" in snappy
    assert "nFeatureSnapIter 30;" in snappy
    assert "implicitFeatureSnap true;" in snappy
    assert "explicitFeatureSnap true;" in snappy
    assert "multiRegionFeatureSnap false;" in snappy


def test_openfoam_c04_runner_applies_relaxed_mesh_quality_overrides(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_relaxed_skew_wsl_v2412.yaml"),
        output_dir=tmp_path,
        dry_run=True,
        backend="dry_run_only",
    )

    assert result["validation"]["passed"] is True
    quality = (tmp_path / "case/system/meshQualityDict").read_text(encoding="utf-8")
    assert "\nminFaceWeight 0.02;" in quality
    assert "\nmaxInternalSkewness 12;" in quality
    assert "\nmaxBoundarySkewness 20;" in quality
    assert "\nminTwist -1;" in quality


def test_openfoam_c04_cli_forwards_runtime_arguments(monkeypatch) -> None:
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return {"validation": {"passed": True}}

    monkeypatch.setattr(cli, "run", fake_run)

    code = cli.main(
        [
            "--config",
            "configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml",
            "--output-dir",
            "_results/openfoam/external_aero_motorbike_rans_snappy/cli_test",
            "--backend",
            "wsl",
        ]
    )

    assert code == 0
    assert captured["config_path"] == Path("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    assert captured["output_dir"] == Path("_results/openfoam/external_aero_motorbike_rans_snappy/cli_test")
    assert captured["dry_run"] is False
    assert captured["backend"] == "wsl"
