from __future__ import annotations

import math

from science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation.postprocess import (
    analytical_pressure_kinematic,
    analytical_surface_cp,
    analytical_velocity,
)


def test_openfoam_c02_surface_cp_formula() -> None:
    assert analytical_surface_cp(0.0) == 1.0
    assert abs(analytical_surface_cp(math.pi / 2.0) + 3.0) < 1e-12
    assert abs(analytical_surface_cp(math.pi) - 1.0) < 1e-12


def test_openfoam_c02_velocity_formula_surface_limits() -> None:
    radius = 0.5
    inlet = 2.0
    stagnation = analytical_velocity(radius, 0.0, radius, inlet)
    top = analytical_velocity(0.0, radius, radius, inlet)

    assert abs(stagnation[0]) < 1e-12
    assert abs(stagnation[1]) < 1e-12
    assert abs(top[0] - 2.0 * inlet) < 1e-12
    assert abs(top[1]) < 1e-12


def test_openfoam_c02_bernoulli_pressure_formula() -> None:
    inlet = 2.0
    p_ref = 0.0
    stagnation_pressure = analytical_pressure_kinematic((0.0, 0.0, 0.0), inlet, p_ref)
    surface_top_pressure = analytical_pressure_kinematic((4.0, 0.0, 0.0), inlet, p_ref)

    assert abs(stagnation_pressure - 2.0) < 1e-12
    assert abs(surface_top_pressure + 6.0) < 1e-12
