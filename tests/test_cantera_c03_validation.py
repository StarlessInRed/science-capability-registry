from __future__ import annotations

import yaml

from science_capability_registry.cantera.c03_counterflow_diffusion_flame.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c03_counterflow_diffusion_flame/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _good_metrics() -> dict:
    species_bounds = {
        "C2H6": {"min": 0.0, "max": 1.0, "finite": True},
        "O2": {"min": 0.0, "max": 0.21, "finite": True},
    }
    return {
        "modes": {
            "no_radiation": {
                "converged": True,
                "peak_temperature_k": 1981.0,
                "flame_position_m": 0.0064,
                "grid_point_count": 96,
                "species_bounds": species_bounds,
            },
            "radiation": {
                "converged": True,
                "peak_temperature_k": 1967.0,
                "flame_position_m": 0.0064,
                "grid_point_count": 96,
                "species_bounds": species_bounds,
            },
        },
        "artifacts": {},
    }


def test_validate_metrics_accepts_reference_like_result() -> None:
    result = validate_metrics(_good_metrics(), _baseline_config())
    assert result["passed"] is True


def test_validate_metrics_rejects_radiation_temperature_increase() -> None:
    metrics = _good_metrics()
    metrics["modes"]["radiation"]["peak_temperature_k"] = 1999.0
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "radiation.peak_temperature_not_higher" in failed

