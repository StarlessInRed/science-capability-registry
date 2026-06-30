from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow.runner import run


def test_openfoam_c03_runner_dry_run_writes_manifest_and_template_case() -> None:
    result = run(
        config_path=Path("configs/openfoam/backward_facing_step_rans_internal_flow/baseline.yaml"),
        output_dir=Path("_results/openfoam/backward_facing_step_rans_internal_flow/test_runner"),
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    output_dir = Path("_results/openfoam/backward_facing_step_rans_internal_flow/test_runner")
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "case/system/controlDict").exists()
    control = (output_dir / "case/system/controlDict").read_text(encoding="utf-8")
    assert "#includeFunc streamlines" not in control
    assert "endTime         80" in control
