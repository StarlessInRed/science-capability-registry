from __future__ import annotations

from pathlib import Path

from science_capability_registry.cantera.c05_reaction_path_analysis.runner import run


def test_c05_runner_dry_run_validates_config_without_solver_execution() -> None:
    result = run(
        config_path=Path("configs/cantera/c05_reaction_path_analysis/baseline.yaml"),
        dry_run=True,
    )
    assert result["validated_config"] is True
    assert result["requires_solver"] == "cantera>=3.2"
    assert "graphviz" in result["requires_renderer"]
