"""Validation for Gmsh C06 multi-solver export contracts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple


class ExportTarget(NamedTuple):
    target_id: str
    solver_family: str
    target_solver: str
    export_format: str
    contract_status: str
    expected_boundary_names: tuple[str, ...]
    expected_element_count_min: int
    max_element_count_delta_fraction: float

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ExportTarget":
        return cls(
            target_id=str(data["target_id"]),
            solver_family=str(data["solver_family"]),
            target_solver=str(data["target_solver"]),
            export_format=str(data["export_format"]),
            contract_status=str(data["contract_status"]),
            expected_boundary_names=tuple(str(name) for name in data["expected_boundary_names"]),
            expected_element_count_min=int(data["expected_element_count_min"]),
            max_element_count_delta_fraction=float(data["max_element_count_delta_fraction"]),
        )


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _targets(config: dict[str, Any]) -> list[ExportTarget]:
    return [ExportTarget.from_mapping(item) for item in config["export_targets"]]


def summarize_export_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    targets = _targets(config)
    target_ids = [target.target_id for target in targets]
    solver_families = {target.solver_family for target in targets}
    required_boundaries = set(config["validation"]["required_boundary_names"])
    boundary_mismatch_count = sum(
        1 for target in targets if not required_boundaries.issubset(set(target.expected_boundary_names))
    )
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "exported_format_count": len({target.export_format for target in targets}),
        "target_count": len(targets),
        "solver_family_count": len(solver_families),
        "declared_target_ids": sorted(target_ids),
        "boundary_name_mismatch_count": boundary_mismatch_count,
        "successful_import_count": sum(1 for target in targets if target.contract_status == "import_smoke_passed"),
        "unit_scale_mismatch_count": 0 if float(config["unit_policy"]["scale_factor"]) == 1.0 else 1,
        "max_element_count_delta_fraction": max(target.max_element_count_delta_fraction for target in targets) if targets else None,
    }
    if validation is not None:
        result["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return result


def validate_export_contract(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    targets = _targets(config)
    target_ids = [target.target_id for target in targets]
    duplicate_ids = sorted(target_id for target_id, count in Counter(target_ids).items() if count > 1)
    required_target_ids = set(config["validation"]["required_target_ids"])
    required_boundaries = set(config["validation"]["required_boundary_names"])
    solver_families = {target.solver_family for target in targets}
    metrics = summarize_export_metrics(config)

    _check(
        checks,
        "export_targets.required_ids",
        required_target_ids.issubset(set(target_ids)),
        f"targets={sorted(target_ids)}, required={sorted(required_target_ids)}",
    )
    _check(
        checks,
        "export_targets.duplicate_ids",
        not duplicate_ids,
        json.dumps({"duplicates": duplicate_ids}, ensure_ascii=False),
    )
    _check(
        checks,
        "export_targets.solver_family_count",
        len(solver_families) >= int(config["validation"]["min_solver_family_count"]),
        json.dumps({"solver_families": sorted(solver_families)}, ensure_ascii=False),
    )
    _check(
        checks,
        "export_targets.boundary_names",
        metrics["boundary_name_mismatch_count"] == 0,
        json.dumps(
            {
                "required_boundary_names": sorted(required_boundaries),
                "targets": {target.target_id: sorted(target.expected_boundary_names) for target in targets},
            },
            ensure_ascii=False,
        ),
    )
    _check(
        checks,
        "unit_policy.scale_factor",
        (not config["unit_policy"]["require_unit_scale_match"]) or float(config["unit_policy"]["scale_factor"]) == 1.0,
        json.dumps(config["unit_policy"], ensure_ascii=False),
    )
    _check(
        checks,
        "orientation_policy.positive_orientation",
        config["orientation_policy"]["require_positive_orientation"] is True,
        json.dumps(config["orientation_policy"], ensure_ascii=False),
    )
    _check(
        checks,
        "export_targets.element_count_delta",
        all(target.max_element_count_delta_fraction <= 0.05 for target in targets),
        json.dumps({target.target_id: target.max_element_count_delta_fraction for target in targets}, ensure_ascii=False),
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh multi-solver export/import contract; no solver import command execution",
        "checks": checks,
        "details": {
            "target_ids": target_ids,
            "duplicate_target_ids": duplicate_ids,
            "solver_families": sorted(solver_families),
            "metrics": metrics,
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_export_contract(config)
    checks = list(validation["checks"])
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)

    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            _check(checks, f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh multi-solver export manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
