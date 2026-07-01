from __future__ import annotations

from pathlib import Path

import yaml

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


def test_openfoam_c06_runner_preserves_sampling_include_when_configured(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("configs/openfoam/dam_break_vof_free_surface/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["validation"]["sampling_parity"] = {
        "required_for_gate": False,
        "status": "passed",
        "source": "native_openfoam_sampling",
        "native_sampling_enabled": True,
        "evidence_id": "dry_run_sampling_include_probe",
    }

    result = run(config=config, output_dir=tmp_path, dry_run=True)

    assert result["validation"]["passed"] is True
    control = (tmp_path / "case/system/controlDict").read_text(encoding="utf-8")
    assert '#sinclude   "sampling"' in control
