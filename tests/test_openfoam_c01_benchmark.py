from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.benchmark import (
    validate_benchmark_matrix,
)


def _write_profile(path: Path, case_id: str, line_id: str, component: str, scale: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "case_id,line_id,time_s,sample_index,x_m,y_m,z_m,x_over_L,y_over_L,Ux_m_s,Uy_m_s,Uz_m_s,U_mag_m_s",
    ]
    for index, s in enumerate([0.0, 0.5, 1.0]):
        ux = scale * s if component == "Ux_m_s" else 0.0
        uy = scale * s if component == "Uy_m_s" else 0.0
        rows.append(f"{case_id},{line_id},0.5,{index},{s * 0.1},0.05,0.005,{s},{s},{ux},{uy},0,{abs(ux) + abs(uy)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _case(root: Path, case_id: str, vertical_scale: float, horizontal_scale: float, max_co: float) -> dict:
    vertical = root / case_id / "vertical.csv"
    horizontal = root / case_id / "horizontal.csv"
    _write_profile(vertical, case_id, "vertical_centerline_Ux", "Ux_m_s", vertical_scale)
    _write_profile(horizontal, case_id, "horizontal_centerline_Uy", "Uy_m_s", horizontal_scale)
    return {
        "validation": {"passed": True},
        "output_dir": root / case_id,
        "metrics": {
            "solver": {"max_courant_number": max_co},
            "postprocess": {
                "profiles": {
                    "vertical_centerline_Ux": {
                        "path": str(vertical),
                        "stats": {"Ux_m_s_range": vertical_scale, "max_abs_dUx_m_s_dy_m": vertical_scale},
                    },
                    "horizontal_centerline_Uy": {
                        "path": str(horizontal),
                        "stats": {"Uy_m_s_range": horizontal_scale, "max_abs_dUy_m_s_dx_m": horizontal_scale},
                    },
                }
            },
        },
    }


def test_openfoam_c01_benchmark_matrix_accepts_expected_trends() -> None:
    root = Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/test_benchmark")
    cases = {
        "baseline_wsl_v2112": _case(root, "baseline_wsl_v2112", 1.0, 1.0, 0.8),
        "mesh_40x40_cfl_matched_wsl_v2112": _case(root, "mesh_40x40_cfl_matched_wsl_v2112", 1.01, 1.01, 0.75),
        "re100_wsl_v2112": _case(root, "re100_wsl_v2112", 1.2, 1.2, 0.7),
        "dt_half_wsl_v2112": _case(root, "dt_half_wsl_v2112", 1.0, 1.0, 0.4),
    }

    result = validate_benchmark_matrix(cases)

    assert result["passed"] is True
    assert result["gate"] == "integration"
