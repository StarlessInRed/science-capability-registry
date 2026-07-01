from __future__ import annotations

from science_capability_registry.registry.cli import main


def test_registry_cli_plan_and_resolve(capsys) -> None:
    assert main(["plan"]) == 0
    plan_output = capsys.readouterr().out
    assert "meshing.gmsh.parametric_geometry_mesh_generation" in plan_output

    assert main(["resolve", "cfd.openfoam.transient_cylinder_vortex_shedding"]) == 0
    resolve_output = capsys.readouterr().out
    assert "benchmark_validated" in resolve_output
    assert "openfoam_C05_case_freeze_finite_domain_strouhal_2026-07-01" in resolve_output
