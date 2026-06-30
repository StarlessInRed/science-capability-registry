from __future__ import annotations

import math
from pathlib import Path

import pytest

from science_capability_registry.openfoam.field_io import CellGeometry
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.config import load_case_config
from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.postprocess import (
    average_state_windows,
    compute_boundary_flux_conservation_proxy,
    compute_jump_ratios,
    locate_shock_position_from_profile,
    normal_shock_sanity_ratios,
    select_x_axis_profile_rows,
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


def test_openfoam_c08_locates_shock_with_configured_search_window() -> None:
    rows = [
        {"x_m": 0.0, "p": 1.0, "rho": 1.0, "T": 1.0, "Ux": 3.0, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 0.1, "p": 8.0, "rho": 4.0, "T": 1.0, "Ux": 1.0, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.1, "p": 2.0, "rho": 1.5, "T": 1.0, "Ux": 2.0, "Uy": 0.0, "Uz": 0.0},
        {"x_m": 1.3, "p": 5.0, "rho": 3.0, "T": 1.7, "Ux": 1.8, "Uy": 0.0, "Uz": 0.0},
    ]

    shock_x = locate_shock_position_from_profile(rows, "p", (1.0, 1.4))

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


def test_openfoam_c08_selects_nearest_cells_for_x_axis_profile() -> None:
    cells = [
        CellGeometry(index=0, center=(0.0, 0.4, 0.0), volume=1.0),
        CellGeometry(index=1, center=(0.0, 0.51, 0.0), volume=1.0),
        CellGeometry(index=2, center=(1.0, 0.49, 0.0), volume=1.0),
        CellGeometry(index=3, center=(1.0, 0.8, 0.0), volume=1.0),
    ]

    rows = select_x_axis_profile_rows(
        cells,
        p_values=[1.0, 2.0, 3.0, 4.0],
        rho_values=[1.1, 2.1, 3.1, 4.1],
        t_values=[1.2, 2.2, 3.2, 4.2],
        u_values=[(1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0), (4.0, 0.0, 0.0)],
        fixed_y_m=0.5,
    )

    assert [row["x_m"] for row in rows] == [0.0, 1.0]
    assert [row["p"] for row in rows] == [2.0, 3.0]


def test_openfoam_c08_writes_shock_and_conservation_artifacts(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")
    config["postprocess"] = {
        **config["postprocess"],
        "shock_search_window_m": [1.0, 1.4],
        "upstream_window_m": [0.9, 1.1],
        "downstream_window_m": [1.5, 1.7],
    }
    metrics = write_shock_metrics(config, tmp_path, _profile_rows())
    conservation = write_conservation_summary(
        tmp_path,
        {
            "method": "boundary_flux_owner_cell_proxy",
            "boundary_flux_mass_imbalance_proxy": 0.0,
            "boundary_flux_total_energy_imbalance_proxy": 0.0,
            "limitation": "fixture",
        },
    )

    assert metrics["available"] is True
    assert metrics["shock_search_window_m"] == [1.0, 1.4]
    assert Path(metrics["profile_path"]).exists()
    assert Path(metrics["path"]).exists()
    assert conservation["available"] is True
    assert conservation["method"] == "boundary_flux_owner_cell_proxy"
    assert Path(conservation["path"]).exists()


def test_openfoam_c08_boundary_flux_proxy_reports_canonical_imbalance_keys(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    poly = case_dir / "constant" / "polyMesh"
    time_dir = case_dir / "1"
    poly.mkdir(parents=True)
    time_dir.mkdir(parents=True)
    (poly / "points").write_text(
        """
8
(
(0 0 0)
(1 0 0)
(1 1 0)
(0 1 0)
(0 0 1)
(1 0 1)
(1 1 1)
(0 1 1)
)
""",
        encoding="utf-8",
    )
    (poly / "faces").write_text(
        """
2
(
4(0 4 7 3)
4(1 2 6 5)
)
""",
        encoding="utf-8",
    )
    (poly / "owner").write_text(
        """
2
(
0
0
)
""",
        encoding="utf-8",
    )
    (poly / "neighbour").write_text(
        """
0
(
)
""",
        encoding="utf-8",
    )
    (poly / "boundary").write_text(
        """
2
(
inlet
{
    type patch;
    nFaces 1;
    startFace 0;
}
outlet
{
    type patch;
    nFaces 1;
    startFace 1;
}
)
""",
        encoding="utf-8",
    )
    (time_dir / "p").write_text("internalField uniform 1;\n", encoding="utf-8")
    (time_dir / "T").write_text("internalField uniform 1;\n", encoding="utf-8")
    (time_dir / "rho").write_text("internalField uniform 1;\n", encoding="utf-8")
    (time_dir / "U").write_text("internalField uniform (1 0 0);\n", encoding="utf-8")
    config = load_case_config("configs/openfoam/compressible_shock_capturing_forward_step/baseline.yaml")

    summary = compute_boundary_flux_conservation_proxy(config, tmp_path)

    assert summary["method"] == "boundary_flux_owner_cell_proxy"
    assert summary["boundary_flux_mass_imbalance_proxy"] == 0.0
    assert summary["boundary_flux_total_energy_imbalance_proxy"] == 0.0
    assert Path(summary["boundary_flux_path"]).exists()
