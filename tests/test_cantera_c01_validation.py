from __future__ import annotations

import yaml

from science_capability_registry.cantera.c01_constant_pressure_ignition.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c01_constant_pressure_ignition/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _summary(ignition_delay_s: float = 4.0e-4) -> dict:
    return {
        "time_point_count": 101,
        "end_time_s": 1.0e-3,
        "initial_temperature_k": 1001.0,
        "final_temperature_k": 2701.0,
        "temperature_rise_k": 1700.0,
        "ignition_delay_s": ignition_delay_s,
        "ignition_delay_method": "max_temperature_derivative",
        "max_temperature_derivative_k_s": 1.0e7,
        "max_temperature_derivative_index": 40,
        "max_temperature_step_k": 17.0,
        "max_pressure_relative_error": 1.0e-12,
        "species_bounds": {
            "OH": {"min": 0.0, "max": 0.01, "finite": True},
            "H": {"min": 0.0, "max": 0.01, "finite": True},
            "H2": {"min": 0.0, "max": 0.3, "finite": True},
            "O2": {"min": 0.0, "max": 0.2, "finite": True},
            "H2O": {"min": 0.0, "max": 0.4, "finite": True},
        },
    }


def _profile() -> dict:
    time_s = [index * 1.0e-5 for index in range(101)]
    temperature_k = [1001.0 + 17.0 * index for index in range(101)]
    pressure_pa = [101325.0 for _ in time_s]
    profile = {
        "time_s": time_s,
        "time_ms": [value * 1.0e3 for value in time_s],
        "temperature_k": temperature_k,
        "pressure_pa": pressure_pa,
        "internal_energy_j_kg": [-1.0e6 for _ in time_s],
        "enthalpy_j_kg": [-5.0e5 for _ in time_s],
    }
    for species in ["OH", "H", "H2", "O2", "H2O"]:
        profile[f"X_{species}"] = [0.0 for _ in time_s]
    return profile


def _metrics(summary: dict | None = None) -> dict:
    return {"summary": summary or _summary(), "profile": _profile(), "artifacts": {}}


def test_c01_validation_accepts_reference_like_metrics() -> None:
    result = validate_metrics(_metrics(), _baseline_config())
    assert result["passed"] is True


def test_c01_validation_rejects_missing_temperature_rise() -> None:
    bad = _summary()
    bad["temperature_rise_k"] = 10.0
    result = validate_metrics(_metrics(bad), _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "temperature.rise" in failed


def test_c01_validation_rejects_missing_profile_species_column() -> None:
    metrics = _metrics()
    del metrics["profile"]["X_OH"]
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "profile.column.X_OH" in failed
