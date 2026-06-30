from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.dam_break_vof_free_surface.runner import run


def test_openfoam_c06_runner_dry_run_writes_manifest_and_template_case() -> None:
    result = run(
        config_path=Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml"),
        output_dir=Path("_results/openfoam/dam_break_vof_free_surface/test_runner"),
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    output_dir = Path("_results/openfoam/dam_break_vof_free_surface/test_runner")
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/0/alpha.water").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "sampling" not in control
    assert "maxCo           0.75" in control
