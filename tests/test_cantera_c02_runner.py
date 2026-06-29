from __future__ import annotations

from pathlib import Path

from science_capability_registry.cantera.c02_freely_propagating_premixed_flame.runner import run


def test_c02_runner_dry_run_validates_config_without_solver_execution() -> None:
    result = run(
        config_path=Path("configs/cantera/c02_freely_propagating_premixed_flame/baseline.yaml"),
        dry_run=True,
    )
    assert result["validated_config"] is True
    assert result["requires_solver"] == "cantera>=3.2"
    assert result["planned_modes"] == [
        "mixture_averaged",
        "mixture_averaged_soret",
        "multicomponent",
        "multicomponent_soret",
    ]
