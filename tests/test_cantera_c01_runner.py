from __future__ import annotations

from pathlib import Path

from science_capability_registry.cantera.c01_constant_pressure_ignition.runner import run


def test_c01_runner_dry_run_validates_config_without_solver_execution() -> None:
    result = run(
        config_path=Path("configs/cantera/c01_constant_pressure_ignition/baseline.yaml"),
        dry_run=True,
    )
    assert result["validated_config"] is True
    assert result["requires_solver"] == "cantera>=3.2"
