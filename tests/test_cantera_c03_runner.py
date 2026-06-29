from __future__ import annotations

from pathlib import Path

from science_capability_registry.cantera.c03_counterflow_diffusion_flame.runner import run


def test_runner_dry_run_validates_config_without_cantera() -> None:
    result = run(
        config_path=Path("configs/cantera/c03_counterflow_diffusion_flame/baseline.yaml"),
        dry_run=True,
    )
    assert result["validated_config"] is True
    assert result["requires_solver"] == "cantera>=3.0"
    assert result["planned_modes"] == ["no_radiation", "radiation"]

