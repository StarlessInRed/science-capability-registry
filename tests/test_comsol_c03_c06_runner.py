from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, NamedTuple

import yaml
from science_capability_registry.comsol.geometry_mesh_import_contract import (
    run as run_c03,
)
from science_capability_registry.comsol.physics_boundary_assignment_contract import (
    run as run_c04,
)
from science_capability_registry.comsol.result_extraction_postprocess_validation import (
    run as run_c06,
)
from science_capability_registry.comsol.study_run_solver_smoke import run as run_c05

CASES: list[tuple[Callable[..., dict], Path, list[str]]] = [
    (
        run_c03,
        Path("configs/comsol/geometry_mesh_import_contract/static_contract.yaml"),
        ["geometry_manifest.json", "mesh_manifest.json", "selection_map.json"],
    ),
    (
        run_c04,
        Path(
            "configs/comsol/physics_boundary_assignment_contract/static_contract.yaml"
        ),
        [
            "physics_assignment_manifest.json",
            "boundary_assignment_manifest.json",
            "unit_policy.json",
        ],
    ),
    (
        run_c05,
        Path("configs/comsol/study_run_solver_smoke/static_contract.yaml"),
        ["solver_manifest.json", "dataset_manifest.json"],
    ),
    (
        run_c06,
        Path(
            "configs/comsol/result_extraction_postprocess_validation/static_contract.yaml"
        ),
        ["export_manifest.json", "probes.csv", "units.json"],
    ),
]


class BoundaryCase(NamedTuple):
    runner: Callable[..., dict]
    config_path: Path
    asset_path: Path
    stage: str
    stage_terms: tuple[str, ...]
    no_claim_terms: tuple[str, ...]


RUNTIME_CASES: list[BoundaryCase] = [
    BoundaryCase(
        run_c03,
        Path(
            "configs/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle.yaml"
        ),
        Path("software/comsol/assets/C03_geometry_mesh_import_contract.yaml"),
        "geometry_mesh_import_contract",
        ("geometry", "mesh", "selection"),
        ("mesh-quality", "double-v"),
    ),
    BoundaryCase(
        run_c04,
        Path(
            "configs/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle.yaml"
        ),
        Path("software/comsol/assets/C04_physics_boundary_assignment_contract.yaml"),
        "physics_boundary_assignment_contract",
        ("physics", "boundary", "assignment"),
        ("solver convergence", "double-v"),
    ),
    BoundaryCase(
        run_c05,
        Path(
            "configs/comsol/study_run_solver_smoke/local_livelink_heat_rectangle.yaml"
        ),
        Path("software/comsol/assets/C05_study_run_solver_smoke.yaml"),
        "study_run_solver_smoke",
        ("study", "solver"),
        ("analytical field validation", "double-v"),
    ),
    BoundaryCase(
        run_c06,
        Path(
            "configs/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle.yaml"
        ),
        Path(
            "software/comsol/assets/C06_result_extraction_postprocess_validation.yaml"
        ),
        "result_extraction_postprocess_validation",
        ("result", "export"),
        ("broader multiphysics correctness", "double-v"),
    ),
]


def test_comsol_c03_c06_static_runners_write_contract_artifacts(tmp_path: Path) -> None:
    for runner, config_path, artifacts in CASES:
        case_output = tmp_path / config_path.parent.name
        result = runner(config_path=config_path, output_dir=case_output, dry_run=True)

        assert result["validation"]["passed"] is True
        assert result["metrics"]["runtime_executed"] is False
        assert result["validation"]["gate"] == "static-readiness"
        for rel_path in [
            *artifacts,
            "manifest.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
        ]:
            assert (case_output / rel_path).exists(), rel_path
        manifest = json.loads(
            (case_output / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["runtime_executed"] is False
        assert "no COMSOL" in (case_output / "validation_report.md").read_text(
            encoding="utf-8"
        )


def test_comsol_c06_static_runner_writes_csv_shaped_probe_contract(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "c06"
    run_c06(
        config_path=Path(
            "configs/comsol/result_extraction_postprocess_validation/static_contract.yaml"
        ),
        output_dir=output_dir,
        dry_run=True,
    )

    probes_text = (output_dir / "probes.csv").read_text(encoding="utf-8")
    assert probes_text.startswith("artifact_path,artifact_role,stage,runtime_executed")
    assert "false" in probes_text


def test_comsol_c03_c06_runtime_dry_run_writes_scripts_without_matlab(
    tmp_path: Path,
) -> None:
    for case in RUNTIME_CASES:
        case_output = tmp_path / case.stage
        result = case.runner(
            config_path=case.config_path, output_dir=case_output, dry_run=True
        )

        assert result["validation"]["passed"] is True
        assert result["validation"]["gate"] == "static-readiness"
        assert result["metrics"]["runtime_status"] == "dry_run_not_executed"
        assert result["metrics"]["matlab_executed"] is False
        assert (case_output / result["metrics"]["script_file"]).exists()
        assert (
            "official replay"
            in "\n".join(result["validation"]["details"]["no_claims"]).lower()
        )
        assert (
            "benchmark validation"
            in "\n".join(result["validation"]["details"]["no_claims"]).lower()
        )


def test_comsol_c03_c06_stage_claim_boundary(tmp_path: Path) -> None:
    catalog = json.loads(
        Path("configs/registry/capability_catalog.json").read_text(encoding="utf-8")
    )
    evidence_index = yaml.safe_load(
        Path("reports/evidence_index.yaml").read_text(encoding="utf-8")
    )
    catalog_by_asset = {entry["asset_id"]: entry for entry in catalog["capabilities"]}
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }

    for case in RUNTIME_CASES:
        result = case.runner(
            config_path=case.config_path, output_dir=tmp_path / case.stage, dry_run=True
        )
        asset = yaml.safe_load(case.asset_path.read_text(encoding="utf-8"))
        catalog_entry = catalog_by_asset[asset["asset_id"]]
        evidence = evidence_by_id[catalog_entry["primary_evidence_id"]]

        assert result["contract"]["stage"] == case.stage
        assert result["validation"]["gate"] in {"static-readiness", "smoke"}
        assert asset["benchmark_status"] == "package_skeleton_created"
        assert catalog_entry["benchmark_status"] == "package_skeleton_created"
        assert catalog_entry["dispatch_status"] == "runtime_smoke_passed"
        assert catalog_entry["current_gate"] == "smoke"
        assert evidence["gate"] == "smoke"
        assert evidence["status"] == "passed"
        assert evidence["evidence_kind"] == "runtime_smoke_report"

        promotion_text = json.dumps(
            {
                "asset_benchmark_status": asset["benchmark_status"],
                "catalog_benchmark_status": catalog_entry["benchmark_status"],
                "catalog_gate": catalog_entry["current_gate"],
                "evidence_gate": evidence["gate"],
            },
            ensure_ascii=False,
        ).lower()
        assert "benchmark_validated" not in promotion_text
        assert "double-v" not in promotion_text
        assert "double_v" not in promotion_text

        stage_text = json.dumps(result["contract"], ensure_ascii=False).lower()
        for term in case.stage_terms:
            assert term in stage_text

        no_claim_text = "\n".join(
            result["validation"]["details"]["no_claims"] + evidence["limitations"]
        ).lower()
        for term in ("official replay", "benchmark validation", *case.no_claim_terms):
            assert term in no_claim_text
