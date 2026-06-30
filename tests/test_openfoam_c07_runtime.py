from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.runtime import (
    parse_check_mesh_log,
    parse_chtmultiregion_log,
    validate_runtime_metrics,
)


def _config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml").read_text(
            encoding="utf-8"
        )
    )


def _mhr_config() -> dict:
    return yaml.safe_load(
        Path(
            "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml"
        ).read_text(encoding="utf-8")
    )


def test_parse_chtmultiregion_log_extracts_regions_residuals_and_completion() -> None:
    log_text = """
Time = 199
Create fluid mesh for region domain0 for time = 0
Create solid mesh for region v_CPU for time = 0
Create solid mesh for region v_fins for time = 0
Solving for fluid region domain0
smoothSolver:  Solving for Ux, Initial residual = 1e-02, Final residual = 1e-05, No Iterations 2
time step continuity errors : sum local = 1e-08, global = 2e-09, cumulative = 3e-08
Solving for solid region v_CPU
PCG:  Solving for T, Initial residual = 2e-02, Final residual = 8e-06, No Iterations 3
Solving for solid region v_fins
PCG:  Solving for T, Initial residual = 3e-02, Final residual = 9e-06, No Iterations 3
Time = 200
"""

    parsed = parse_chtmultiregion_log(log_text)

    assert parsed["started"] is True
    assert parsed["fatal_error_detected"] is False
    assert parsed["final_time"] == 200.0
    assert parsed["iteration_count"] == 2
    assert parsed["regions_seen"] == ["domain0", "v_CPU", "v_fins"]
    assert parsed["last_residuals"]["v_CPU"]["T"]["final"] == 8e-06
    assert parsed["last_continuity"]["region"] == "domain0"


def test_parse_chtmultiregion_log_extracts_heater_radiation_regions() -> None:
    log_text = """
Time = 2
Solving for fluid region bottomAir
DILUPBiCGStab:  Solving for h, Initial residual = 0.9624945, Final residual = 0.08369737, No Iterations 1
time step continuity errors : sum local = 0.1656838, global = -6.938969e-18, cumulative = -0.05802718
Solving for fluid region topAir
DILUPBiCGStab:  Solving for h, Initial residual = 0.3950533, Final residual = 0.01300888, No Iterations 1
Solving for solid region heater
DICPCG:  Solving for h, Initial residual = 0.1877447, Final residual = 0.01465519, No Iterations 1
Solving for solid region leftSolid
DICPCG:  Solving for h, Initial residual = 0.687802, Final residual = 0.05339896, No Iterations 1
Solving for solid region rightSolid
DICPCG:  Solving for h, Initial residual = 0.633732, Final residual = 0.04837411, No Iterations 1
End
"""

    parsed = parse_chtmultiregion_log(log_text)

    assert parsed["final_time"] == 2.0
    assert parsed["regions_seen"] == ["bottomAir", "heater", "leftSolid", "rightSolid", "topAir"]
    assert parsed["last_residuals"]["bottomAir"]["h"]["final"] == 0.08369737


def test_parse_chtmultiregion_log_detects_real_fatal_error_but_not_fpe_trap_notice() -> None:
    trap_notice = "trapFpe: Floating point exception trapping enabled\nTime = 1\n"
    fatal = "Time = 1\nFloating point exception\n"

    assert parse_chtmultiregion_log(trap_notice)["fatal_error_detected"] is False
    assert parse_chtmultiregion_log(fatal)["fatal_error_detected"] is True


def test_parse_check_mesh_log_extracts_mesh_quality_signal() -> None:
    log_text = """
Create mesh for time = 0 region domain0
cells:           100
Max aspect ratio = 12.5
Max non-orthogonality = 61.2 average = 12.0
Max skewness = 2.1 OK.
Mesh OK.
"""

    parsed = parse_check_mesh_log(log_text)

    assert parsed["ran"] is True
    assert parsed["mesh_ok"] is True
    assert parsed["regions_seen"] == ["domain0"]
    assert parsed["cell_count"] == [100]
    assert parsed["max_non_orthogonality"] == 61.2
    assert parsed["max_skewness"] == 2.1
    assert parsed["max_aspect_ratio"] == 12.5


def _minimal_metrics(config: dict, *, residual: float = 1.0e-5, max_temperature: float = 360.0) -> dict:
    regions = [*config["regions"]["fluid"], *config["regions"]["solid"]]
    temperature_rows = []
    for index, region in enumerate(regions):
        temperature_rows.append(
            {
                "region": region,
                "available": True,
                "finite": True,
                "min_T_K": 300.0,
                "max_T_K": max_temperature if index == 0 else min(340.0 + index, max_temperature),
            }
        )
    return {
        "runtime": {"commands": [{"command": command, "returncode": 0} for command in [
            *config["mesh_workflow"]["command_sequence"],
            *config["radiation"]["preprocessing_commands"],
            *config["solver"]["command_sequence"],
            *[command for command in config["postprocess"]["command_sequence"] if not command.startswith("python:")],
        ]]},
        "mesh": {"mesh_ok": True},
        "solver": {
            "started": True,
            "fatal_error_detected": False,
            "final_time": float(config["numerics"]["control"]["end_time_iterations"]),
            "regions_seen": regions,
            "last_residuals": {regions[0]: {"T": {"final": residual}}},
        },
        "postprocess": {
            "temperatures": {
                "regions": temperature_rows
            },
            "interfaces": {"available": True, "interfaces": [{"interface": "domain0_to_v_CPU", "mean_abs_delta_T_K": 12.0}]},
        },
    }


def test_openfoam_c07_runtime_validation_accepts_minimal_smoke_metrics(tmp_path: Path) -> None:
    config = _config()
    metrics = _minimal_metrics(config)
    for rel_path in config["outputs"]["expected_outputs"]:
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    assert validation["passed"] is True
    assert validation["benchmark_status"] == "runtime_smoke_verified"


def test_openfoam_c07_runtime_validation_rejects_bad_residual(tmp_path: Path) -> None:
    config = _config()
    metrics = _minimal_metrics(config, residual=2.0e-3)

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    assert validation["passed"] is False
    failed = {check["name"] for check in validation["checks"] if not check["passed"]}
    assert "solver.final_residual_threshold" in failed


def test_openfoam_c07_runtime_validation_rejects_temperature_out_of_bounds(tmp_path: Path) -> None:
    config = _config()
    metrics = _minimal_metrics(config, max_temperature=700.0)

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    assert validation["passed"] is False
    failed = {check["name"] for check in validation["checks"] if not check["passed"]}
    assert "postprocess.temperature_bounds" in failed


def test_openfoam_c07_runtime_validation_accepts_heater_radiation_smoke_metrics(tmp_path: Path) -> None:
    config = _mhr_config()
    metrics = _minimal_metrics(config, residual=8.0e-2, max_temperature=500.0)
    for rel_path in [*config["outputs"]["expected_outputs"], *config["radiation"]["required_generated_files"]]:
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok\n", encoding="utf-8")

    validation = validate_runtime_metrics(metrics, config, tmp_path)

    assert validation["passed"] is True
    assert validation["gate"] == "smoke"
