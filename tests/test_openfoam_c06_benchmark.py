from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.dam_break_vof_free_surface.benchmark import validate_benchmark_matrix


PROFILE_NAMES = [
    "front_position_history",
    "water_volume_history",
    "alpha_bounds_history",
    "gauge_interface_height_history",
    "free_surface_profile_final",
]


def _case(root: Path, case_id: str, front: float, volume: float) -> dict:
    profiles = {}
    root.mkdir(parents=True, exist_ok=True)
    for name in PROFILE_NAMES:
        path = root / f"{case_id}_{name}.csv"
        path.write_text("x\n1\n", encoding="utf-8")
        profiles[name] = {"path": str(path)}
    return {
        "validation": {"passed": True},
        "output_dir": root / case_id,
        "metrics": {
            "postprocess": {
                "front": {"front_x_m": front},
                "volume": {"water_volume_m3": volume, "relative_error": 0.0},
                "profiles": profiles,
            }
        },
    }


def test_openfoam_c06_benchmark_matrix_accepts_expected_trends() -> None:
    root = Path("_results/openfoam/dam_break_vof_free_surface/test_benchmark")
    cases = {
        "baseline_wsl_v2112": _case(root, "baseline_wsl_v2112", 0.25, 1.0),
        "mesh_refined_wsl_v2112": _case(root, "mesh_refined_wsl_v2112", 0.24, 1.0),
        "gravity_half_wsl_v2112": _case(root, "gravity_half_wsl_v2112", 0.20, 1.0),
        "water_height_125pct_wsl_v2112": _case(root, "water_height_125pct_wsl_v2112", 0.25, 1.25),
    }
    result = validate_benchmark_matrix(cases)
    assert result["passed"] is True
