from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.gmsh.boundary_physical_group_contract.runner import run


def test_gmsh_c02_runner_dry_run_writes_contract_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/gmsh/boundary_physical_group_contract/baseline.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["role_mapping_coverage"] == 1.0
    for rel_path in [
        "physical_group_map.json",
        "boundary_contract.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        assert (tmp_path / rel_path).exists()

    contract = json.loads((tmp_path / "boundary_contract.json").read_text(encoding="utf-8"))
    group_map = json.loads((tmp_path / "physical_group_map.json").read_text(encoding="utf-8"))
    assert contract["target_solver"] == "openfoam"
    assert "fluid_domain" in group_map["groups_by_name"]
    assert "wall" in group_map["groups_by_role"]
    assert "does not claim Gmsh mesh generation success" in (tmp_path / "validation_report.md").read_text(encoding="utf-8")
