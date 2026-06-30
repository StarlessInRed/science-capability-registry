from __future__ import annotations

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.runtime import parse_pimplefoam_log


def test_openfoam_c05_parse_pimplefoam_log_extracts_health_signals() -> None:
    log_text = """
Starting time loop
Time = 0.05
Courant Number mean: 0.1 max: 0.7
DILUPBiCGStab:  Solving for Ux, Initial residual = 1e-02, Final residual = 1e-05, No Iterations 2
time step continuity errors : sum local = 1e-08, global = 0, cumulative = 1e-08
Time = 0.1
Courant Number mean: 0.2 max: 0.9
DILUPBiCGStab:  Solving for p, Initial residual = 1e-03, Final residual = 1e-06, No Iterations 3
"""

    parsed = parse_pimplefoam_log(log_text)

    assert parsed["started"] is True
    assert parsed["fatal_error_detected"] is False
    assert parsed["final_time"] == 0.1
    assert parsed["max_courant_number"] == 0.9
    assert parsed["last_residuals"]["p"]["final"] == 1e-06
    assert parsed["last_continuity"]["sum_local"] == 1e-08


def test_openfoam_c05_parse_pimplefoam_log_detects_true_fpe() -> None:
    parsed = parse_pimplefoam_log("Time = 0.05\nFloating point exception (core dumped)\n")

    assert parsed["fatal_error_detected"] is True


def test_openfoam_c05_parse_pimplefoam_log_detects_sigfpe_stack() -> None:
    parsed = parse_pimplefoam_log("Time = 0.3\n#1  Foam::sigFpe::sigHandler(int) at ??:?\n")

    assert parsed["fatal_error_detected"] is True
