from __future__ import annotations

import yaml

from science_capability_registry.cantera.c04_extinction_strain_rate.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c04_extinction_strain_rate/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def test_c04_validation_accepts_reference_like_metrics() -> None:
    metrics = {
        "history": {
            "alpha": [1.0, 2.0, 3.0],
            "peak_temperature_k": [1900.0, 1700.0, 500.0],
            "max_strain_rate_1_s": [2400.0, 5000.0, 7500.0],
            "status": ["burning", "burning", "extinguished"],
        },
        "extinction": {
            "peak_temperature_k": 1700.0,
            "strain_rates_1_s": {
                "mean": 1000.0,
                "max": 5000.0,
                "potential_flow_fuel": 3000.0,
                "potential_flow_oxidizer": 5000.0,
                "stoichiometric": 2000.0,
            },
        },
        "artifacts": {},
    }
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is True


def test_c04_validation_rejects_missing_extinguished_state() -> None:
    metrics = {
        "history": {
            "alpha": [1.0, 2.0],
            "peak_temperature_k": [1900.0, 1700.0],
            "max_strain_rate_1_s": [2400.0, 5000.0],
            "status": ["burning", "burning"],
        },
        "extinction": {
            "peak_temperature_k": 1700.0,
            "strain_rates_1_s": {
                "mean": 1000.0,
                "max": 5000.0,
                "potential_flow_fuel": 3000.0,
                "potential_flow_oxidizer": 5000.0,
                "stoichiometric": 2000.0,
            },
        },
        "artifacts": {},
    }
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "history.has_extinguished_solution" in failed
