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
    assert "nu              0.01" in (output_dir / "case/constant/transportProperties").read_text(encoding="utf-8")
