from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.runner import run


def test_openfoam_c07_runner_dry_run_writes_manifest_and_multiregion_case() -> None:
    output_dir = Path("_results/openfoam/conjugate_heat_transfer_cooling/test_runner")
    result = run(
        config_path=Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["runtime_profile"] == "openfoam_com_v2112_cht"
    assert "mpirun --oversubscribe -np 10 chtMultiRegionSimpleFoam -parallel" in result["solver_commands"]
    assert "mpirun --oversubscribe -np 10 splitMeshRegions -cellZones -overwrite -parallel" in result["mesh_commands"]
    assert result["interfaces"] == ["domain0_to_v_CPU", "domain0_to_v_fins", "v_CPU_to_v_fins"]

    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/constant/regionProperties").exists()
    assert (output_dir / "case/constant/triSurface/Cabinet_withMesh.obj.gz").exists()
    assert (output_dir / "case/constant/triSurface/MRF_region.obj.gz").exists()
    assert (output_dir / "case/0/domain0/T").exists()
    assert (output_dir / "case/0/v_CPU/T").exists()
    assert (output_dir / "case/0/v_fins/T").exists()

    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert '#include    "probes"' not in control
    assert "endTime         200" in control
    assert "writeFormat     ascii" in control

    fv_options = (output_dir / "case/system/v_CPU/fvOptions").read_text(encoding="utf-8")
    assert "h           ( 100 0 );" in fv_options


def test_openfoam_c07_runner_dry_run_writes_heater_radiation_manifest() -> None:
    output_dir = Path("_results/openfoam/conjugate_heat_transfer_cooling/test_runner_mhr")
    result = run(
        config_path=Path(
            "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml"
        ),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["template"]["source_profile_key"] == "c07_multi_region_heater_radiation"
    assert result["regions"]["fluid"] == ["bottomAir", "topAir"]
    assert result["regions"]["solid"] == ["heater", "leftSolid", "rightSolid"]
    assert "faceAgglomerate -region bottomAir" in result["radiation_commands"]
    assert "viewFactorsGen -region topAir" in result["radiation_commands"]
    assert "chtMultiRegionSimpleFoam" in result["solver_commands"]

    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/constant/regionProperties").exists()
    assert (output_dir / "case/0.orig/T").exists()
    assert (output_dir / "case/system/heater/changeDictionaryDict").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "multiRegion" not in control
    heater_change_dict = (output_dir / "case/system/heater/changeDictionaryDict").read_text(encoding="utf-8")
    assert "value           uniform 500;" in heater_change_dict


def test_openfoam_c07_runner_dry_run_patches_heater_temperature_perturbation() -> None:
    output_dir = Path("_results/openfoam/conjugate_heat_transfer_cooling/test_runner_mhr_heater_perturb")
    result = run(
        config_path=Path(
            "configs/openfoam/conjugate_heat_transfer_cooling/perturb_heater_temperature_high_wsl_v2112.yaml"
        ),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["validation_targets"]["matrix_role"] == "heater_temperature_high"
    heater_change_dict = (output_dir / "case/system/heater/changeDictionaryDict").read_text(encoding="utf-8")
    assert "value           uniform 550;" in heater_change_dict


def test_openfoam_c07_runner_dry_run_patches_airflow_perturbation() -> None:
    output_dir = Path("_results/openfoam/conjugate_heat_transfer_cooling/test_runner_mhr_airflow_perturb")
    result = run(
        config_path=Path("configs/openfoam/conjugate_heat_transfer_cooling/perturb_airflow_high_wsl_v2112.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["validation_targets"]["matrix_role"] == "airflow_high"
    top_air = (output_dir / "case/system/topAir/changeDictionaryDict").read_text(encoding="utf-8")
    assert "internalField   uniform (0.2 0 0);" in top_air
    assert "value           uniform (0.2 0 0);" in top_air


def test_openfoam_c07_runner_dry_run_patches_mesh_refinement_perturbation() -> None:
    output_dir = Path("_results/openfoam/conjugate_heat_transfer_cooling/test_runner_mhr_mesh_perturb")
    result = run(
        config_path=Path("configs/openfoam/conjugate_heat_transfer_cooling/perturb_mesh_refinement_wsl_v2112.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["validation_targets"]["matrix_role"] == "mesh_refinement"
    block_mesh = (output_dir / "case/system/blockMeshDict").read_text(encoding="utf-8")
    assert "hex (0 1 2 3 4 5 6 7) (36 12 12) simpleGrading" in block_mesh
