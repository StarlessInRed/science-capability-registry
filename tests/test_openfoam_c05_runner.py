from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.runner import run


def test_openfoam_c05_runner_dry_run_writes_manifest_and_force_coeffs() -> None:
    output_dir = Path("_results/openfoam/transient_cylinder_vortex_shedding/test_runner")
    result = run(
        config_path=Path("configs/openfoam/transient_cylinder_vortex_shedding/baseline_cylinder2d.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/system/controlDict").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "forceCoeffs1" in control
    assert "DMDs/stdmd01" not in control
    assert "nu              0.0012" in (output_dir / "case/constant/transportProperties").read_text(encoding="utf-8")
    assert result["strouhal_reference_policy"]["source_id"] == "openfoam_C05_strouhal_reference_policy_2026-07-01"
    assert any(
        check["name"] == "manifest.section.strouhal_reference_policy" and check["passed"]
        for check in result["validation"]["checks"]
    )
    assert any(
        check["name"] == "strouhal_reference_policy.target_range_locked" and check["passed"]
        for check in result["validation"]["checks"]
    )


def test_openfoam_c05_runner_dry_run_writes_adjustable_time_controls() -> None:
    output_dir = Path("_results/openfoam/transient_cylinder_vortex_shedding/test_runner_strouhal")
    result = run(
        config_path=Path("configs/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112.yaml"),
        output_dir=output_dir,
        dry_run=True,
        backend="dry_run_only",
    )

    assert result["validation"]["passed"] is True
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "forceCoeffs1" not in control
    assert "adjustTimeStep  yes" in control
    assert "maxCo           0.5" in control
    assert "maxDeltaT       0.001" in control
