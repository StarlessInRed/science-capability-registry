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
