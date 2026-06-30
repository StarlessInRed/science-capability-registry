from __future__ import annotations

import math
from pathlib import Path

import pytest

from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.config import load_case_config
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.postprocess import (
    average_state_windows,
    compute_jump_ratios,
    locate_shock_position_from_profile,
    normal_shock_sanity_ratios,
    summarize_field_extrema,
    write_conservation_summary,
    write_shock_metrics,
)


def _profile_rows() -> list[dict[str, float]]:
    return [
        {"x_m": 0.9, "p": 1.0, "rho": 1.0, "T": 1.0, "Ux": 3.0, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.1, "p": 1.1, "rho": 1.1, "T": 1.0, "Ux": 2.8, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.3, "p": 5.0, "rho": 3.0, "T": 1.7, "Ux": 1.8, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.5, "p": 5.3, "rho": 3.2, "T": 1.8, "Ux": 1.6, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.7, "p": 5.4, "rho": 3.3, "T": 1.8, "Ux": 1.5, "Uy": 0.0, "Uz": 0.0},
    ]


def test_openfoam_c08_locates_shock_from_pressure_gradient() -> None:
    shock_x = locate_shock_position_from_profile(_profile_rows(), "p")
    assert math.isclose(shock_x, 1.2)


def test_openfoam_c08_average_windows_and_jump_ratios() -> None:
    windows = average_state_windows(_profile_rows(), (0.9, 1.1), (1.5, 1.7))
    jumps = compute_jump_ratios(windows["upstream"], windows["downstream"])

    assert jumps["pressure_jump_ratio"] > 1.0
    assert jumps["density_jump_ratio"] > 1.0


def test_openfoam_c08_windows_reject_overlap() -> None:
    with pytest.raises(ValueError, match="non-overlapping"):
        average_state_windows(_profile_rows(), (1.0, 1.4), (1.3, 1.7))


def test_openfoam_c08_normal_shock_sanity_ratios_are_supersonic_only() -> None:
    ratios = normal_shock_sanity_ratios(3.0, 1.4)
    assert ratios["pressure_jump_ratio"] > 1.0
    assert ratios["density_jump_ratio"] > 1.0

    with pytest.raises(ValueError, match="supersonic"):
        normal_shock_sanity_ratios(0.8, 1.4)


def test_openfoam_c08_field_extrema_catches_nonfinite_and_negative_values() -> None:
    summary = summarize_field_extrema({"p": [1.0, 2.0], "rho": [1.0, -0.1], "T": [1.0, math.nan], "U": [(1.0, 0.0, 0.0)]})

    assert summary["p"]["finite"] is True
    assert summary["rho"]["min"] < 0.0
    assert summary["T"]["finite"] is False
    assert summary["U"]["available"] is True


def test_openfoam_c08_writes_shock_and_conservation_artifacts(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    metrics = write_shock_metrics(config, tmp_path, _profile_rows())
    conservation = write_conservation_summary(tmp_path, 0.0, 0.0)

    assert metrics["available"] is True
    assert Path(metrics["profile_path"]).exists()
    assert Path(metrics["path"]).exists()
    assert conservation["available"] is True
    assert Path(conservation["path"]).exists()
