from __future__ import annotations

from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.runtime import (
    parse_check_mesh_log,
    parse_icofoam_log,
)


def test_openfoam_c01_parse_icofoam_log_extracts_runtime_health() -> None:
    log = """
Starting time loop

Time = 0.005

Courant Number mean: 0 max: 0
smoothSolver:  Solving for Ux, Initial residual = 1, Final residual = 8.90511e-06, No Iterations 19
DICPCG:  Solving for p, Initial residual = 1, Final residual = 0.0492854, No Iterations 12
time step continuity errors : sum local = 0.000466513, global = -1.79995e-19, cumulative = -1.79995e-19

Time = 0.5

Courant Number mean: 0.112 max: 0.44
smoothSolver:  Solving for Ux, Initial residual = 0.01, Final residual = 1e-07, No Iterations 2
DICPCG:  Solving for pFinal, Initial residual = 0.02, Final residual = 2e-08, No Iterations 8
time step continuity errors : sum local = 1e-09, global = 2e-20, cumulative = 3e-20
End
"""

    result = parse_icofoam_log(log)

    assert result["started"] is True
    assert result["fatal_error_detected"] is False
    assert result["final_time"] == 0.5
    assert result["max_courant_number"] == 0.44
    assert result["last_residuals"]["pFinal"]["final"] == 2e-08
    assert result["last_continuity"]["sum_local"] == 1e-09


def test_openfoam_c01_parse_icofoam_log_detects_fatal_error() -> None:
    result = parse_icofoam_log("FOAM FATAL IO ERROR: missing pFinal")

    assert result["fatal_error_detected"] is True
    assert result["final_time"] is None

def test_openfoam_c01_parse_icofoam_log_ignores_sigfpe_trap_notice() -> None:
    result = parse_icofoam_log("trapFpe: Floating point exception trapping enabled (FOAM_SIGFPE).")

    assert result["fatal_error_detected"] is False

def test_openfoam_c01_parse_check_mesh_log_detects_ok_mesh() -> None:
    result = parse_check_mesh_log("Checking topology...\nMesh OK.\nEnd")

    assert result["ran"] is True
    assert result["mesh_ok"] is True
    assert result["fatal_error_detected"] is False
