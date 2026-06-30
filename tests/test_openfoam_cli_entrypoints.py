from __future__ import annotations

from pathlib import Path


def test_openfoam_c02_c04_c08_console_scripts_are_registered() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'science-openfoam-c02 = "science_capability_registry.openfoam.potential_flow_cylinder_analytical_validation.cli:main"' in pyproject
    assert 'science-openfoam-c04 = "science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.cli:main"' in pyproject
    assert 'science-openfoam-c08 = "science_capability_registry.openfoam.compressible_shock_capturing_forward_step.cli:main"' in pyproject
