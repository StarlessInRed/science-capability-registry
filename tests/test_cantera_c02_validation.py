from __future__ import annotations

import yaml

from science_capability_registry.cantera.c02_freely_propagating_premixed_flame.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c02_freely_propagating_premixed_flame/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _mode_metrics(flame_speed: float = 1.1) -> dict:
    return {
        "flame_speed_m_s": flame_speed,
        "peak_temperature_k": 2200.0,
        "burned_temperature_k": 2200.0,
        "unburned_temperature_k": 300.0,
        "burned_temperature_rise_k": 1900.0,
        "max_heat_release_rate_w_m3": 1.0e9,
        "grid_point_count": 60,
        "species_bounds": {
            "O2": {"min": 0.0, "max": 0.2, "finite": True},
            "H2": {"min": 0.0, "max": 0.2, "finite": True},
            "H2O": {"min": 0.0, "max": 0.4, "finite": True},
        },
    }


def test_c02_validation_accepts_reference_like_metrics() -> None:
    metrics = {
        "modes": {
            "mixture_averaged": _mode_metrics(),
            "mixture_averaged_soret": _mode_metrics(),
            "multicomponent": _mode_metrics(),
            "multicomponent_soret": _mode_metrics(),
        },
        "artifacts": {},
    }
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is True


def test_c02_validation_rejects_unphysical_flame_speed() -> None:
    metrics = {
        "modes": {
            "mixture_averaged": _mode_metrics(flame_speed=-0.1),
            "mixture_averaged_soret": _mode_metrics(),
            "multicomponent": _mode_metrics(),
            "multicomponent_soret": _mode_metrics(),
        },
        "artifacts": {},
    }
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "mode.mixture_averaged.flame_speed_finite" in failed
