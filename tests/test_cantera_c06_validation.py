from __future__ import annotations

import yaml

from science_capability_registry.cantera.c06_mechanism_reduction.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c06_mechanism_reduction/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _metrics() -> dict:
    ranking = [
        {"rank": index + 1, "score": 1.0 - index * 1.0e-4, "equation": f"R{index}"}
        for index in range(900)
    ]
    reductions = []
    for count in [100, 200, 300, 400, 600, 800]:
        reductions.append(
            {
                "requested_reaction_count": count,
                "species_count": max(10, count // 3),
                "reaction_count": count,
                "time_point_count": 50,
                "ignition_delay_ms": 10.0,
                "ignition_delay_relative_error": 0.1 if count == 800 else 0.4,
                "final_temperature_k": 2500.0,
                "final_temperature_error_k": 100.0 if count == 800 else 300.0,
                "reload_check": {
                    "loaded": True,
                    "species_count": max(10, count // 3),
                    "reaction_count": count,
                    "contains_always_include_species": True,
                },
            }
        )
    return {
        "baseline": {
            "species_count": 1200,
            "reaction_count": 5000,
            "summary": {
                "time_point_count": 100,
                "final_temperature_k": 2600.0,
                "temperature_rise_k": 1600.0,
                "ignition_delay_ms": 9.0,
            },
        },
        "reaction_ranking": ranking,
        "reductions": reductions,
        "artifacts": {},
    }


def test_c06_validation_accepts_reference_like_metrics() -> None:
    result = validate_metrics(_metrics(), _baseline_config())
    assert result["passed"] is True


def test_c06_validation_rejects_unsorted_ranking() -> None:
    metrics = _metrics()
    metrics["reaction_ranking"][0]["score"] = 0.1
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "ranking.sorted" in failed
