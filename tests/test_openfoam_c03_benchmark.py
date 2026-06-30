from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.backward_facing_step_rans_internal_flow.benchmark import validate_benchmark_matrix


def _case(root: Path, case_id: str, pressure_drop: float, max_speed: float) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name in ["velocity_profiles", "lower_wall_shear", "pressure_coefficient", "yplus_summary"]:
        path = root / f"{case_id}_{name}.csv"
        path.write_text("x\n1\n", encoding="utf-8")
        paths[name] = path
    return {
        "validation": {"passed": True},
        "output_dir": root / case_id,
        "metrics": {
            "postprocess": {
                "pressure": {"pressure_drop_kinematic_m2_s2": pressure_drop},
                "field_stats": {"max_speed_m_s": max_speed},
                "profiles": {name: {"path": str(path)} for name, path in paths.items()},
            }
        },
    }


def test_openfoam_c03_benchmark_matrix_accepts_expected_trends() -> None:
    root = Path("_results/openfoam/backward_facing_step_rans_internal_flow/test_benchmark")
    cases = {
        "baseline_wsl_v2112": _case(root, "baseline_wsl_v2112", 10.0, 10.0),
        "mesh_refined_wsl_v2112": _case(root, "mesh_refined_wsl_v2112", 9.0, 10.2),
        "inlet_velocity_high_wsl_v2112": _case(root, "inlet_velocity_high_wsl_v2112", 20.0, 15.0),
        "inlet_velocity_low_wsl_v2112": _case(root, "inlet_velocity_low_wsl_v2112", 5.0, 7.0),
    }
    result = validate_benchmark_matrix(cases)
    assert result["passed"] is True
