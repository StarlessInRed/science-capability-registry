from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.openfoam.lid_driven_cavity_incompressible_laminar.runner import (
    run,
)


def test_openfoam_c01_runner_dry_run_writes_manifest_and_case_files() -> None:
    result = run(
        config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
        output_dir=Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/test_runner"),
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["backend"]["type"] == "dry_run_only"
    assert result["solver_commands"] == ["icoFoam"]
    output_dir = Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/test_runner")
    assert (output_dir / "manifest.json").exists()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["validation"]["scope"] == "dry-run manifest and generated case files only"
    assert manifest["postprocess_commands"] == ["python:write_centerline_profiles"]

    for rel_path in [
        "case/0/U",
        "case/0/p",
        "case/constant/transportProperties",
        "case/system/blockMeshDict",
        "case/system/controlDict",
        "case/system/fvSchemes",
        "case/system/fvSolution",
    ]:
        assert (output_dir / rel_path).exists()

    fv_solution = (output_dir / "case/system/fvSolution").read_text(encoding="utf-8")
    assert "pFinal" in fv_solution
    assert "$p;" in fv_solution


def test_openfoam_c01_runner_rejects_solver_execution_without_backend() -> None:
    try:
        run(
            config_path=Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml"),
            dry_run=False,
        )
    except ValueError as exc:
        assert "dry_run=True" in str(exc)
    else:
        raise AssertionError("Expected dry-run skeleton to reject solver execution.")
