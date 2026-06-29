from __future__ import annotations

import yaml

from science_capability_registry.cantera.c05_reaction_path_analysis.validation import (
    validate_metrics,
)


def _baseline_config() -> dict:
    with open(
        "configs/cantera/c05_reaction_path_analysis/baseline.yaml",
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _metrics() -> dict:
    return {
        "element": "N",
        "label_threshold": 0.01,
        "reactor_state": {
            "final_temperature_k": 1901.0,
            "final_pressure_pa": 2.0e5,
            "final_time_s": 0.01,
            "step_count": 100,
        },
        "nodes": ["N", "N2", "NO", "NNH", "HCN", "NH", "NCO"],
        "path_summary": {
            "node_count": 5,
            "edge_count": 6,
            "significant_edge_count": 2,
            "max_abs_net_flux": 1.0e-3,
            "top_edges": [
                {
                    "source": "N2",
                    "target": "NNH",
                    "forward_flux": 0.01,
                    "reverse_flux": -0.009,
                    "net_flux": 0.001,
                    "abs_net_flux": 0.001,
                }
            ],
        },
        "artifacts": {},
    }


def test_c05_validation_accepts_reference_like_metrics() -> None:
    result = validate_metrics(_metrics(), _baseline_config())
    assert result["passed"] is True


def test_c05_validation_rejects_missing_significant_edges() -> None:
    metrics = _metrics()
    metrics["path_summary"]["significant_edge_count"] = 0
    result = validate_metrics(metrics, _baseline_config())
    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "diagram.significant_edges" in failed
