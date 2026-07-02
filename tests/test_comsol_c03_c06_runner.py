from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from science_capability_registry.comsol.geometry_mesh_import_contract import run as run_c03
from science_capability_registry.comsol.physics_boundary_assignment_contract import run as run_c04
from science_capability_registry.comsol.result_extraction_postprocess_validation import run as run_c06
from science_capability_registry.comsol.study_run_solver_smoke import run as run_c05

CASES: list[tuple[Callable[..., dict], Path, list[str]]] = [
    (
        run_c03,
        Path("configs/comsol/geometry_mesh_import_contract/static_contract.yaml"),
        ["geometry_manifest.json", "mesh_manifest.json", "selection_map.json"],
    ),
    (
        run_c04,
        Path("configs/comsol/physics_boundary_assignment_contract/static_contract.yaml"),
        ["physics_assignment_manifest.json", "boundary_assignment_manifest.json", "unit_policy.json"],
    ),
    (
        run_c05,
        Path("configs/comsol/study_run_solver_smoke/static_contract.yaml"),
        ["solver_manifest.json", "dataset_manifest.json"],
    ),
    (
        run_c06,
        Path("configs/comsol/result_extraction_postprocess_validation/static_contract.yaml"),
        ["export_manifest.json", "probes.csv", "units.json"],
    ),
]


def test_comsol_c03_c06_static_runners_write_contract_artifacts(tmp_path: Path) -> None:
    for runner, config_path, artifacts in CASES:
        case_output = tmp_path / config_path.parent.name
        result = runner(config_path=config_path, output_dir=case_output, dry_run=True)

        assert result["validation"]["passed"] is True
        assert result["metrics"]["runtime_executed"] is False
        assert result["validation"]["gate"] == "static-readiness"
        for rel_path in [*artifacts, "manifest.json", "metrics.json", "validation.json", "validation_report.md"]:
            assert (case_output / rel_path).exists(), rel_path
        manifest = json.loads((case_output / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["runtime_executed"] is False
        assert "no COMSOL" in (case_output / "validation_report.md").read_text(encoding="utf-8")


def test_comsol_c06_static_runner_writes_csv_shaped_probe_contract(tmp_path: Path) -> None:
    output_dir = tmp_path / "c06"
    run_c06(
        config_path=Path("configs/comsol/result_extraction_postprocess_validation/static_contract.yaml"),
        output_dir=output_dir,
        dry_run=True,
    )

    probes_text = (output_dir / "probes.csv").read_text(encoding="utf-8")
    assert probes_text.startswith("artifact_path,artifact_role,stage,runtime_executed")
    assert "false" in probes_text
