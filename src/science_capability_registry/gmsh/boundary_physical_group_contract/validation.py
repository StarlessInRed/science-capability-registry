"""Validation for Gmsh C02 physical group contracts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple


class BoundaryGroup(NamedTuple):
    name: str
    dimension: int
    role: str
    required: bool
    downstream_aliases: tuple[str, ...]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "BoundaryGroup":
        return cls(
            name=str(data["name"]),
            dimension=int(data["dimension"]),
            role=str(data["role"]),
            required=bool(data["required"]),
            downstream_aliases=tuple(str(alias) for alias in data["downstream_aliases"]),
        )


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _groups(config: dict[str, Any]) -> list[BoundaryGroup]:
    return [BoundaryGroup.from_mapping(item) for item in config["physical_groups"]]


def _dimension_role_errors(groups: list[BoundaryGroup], geometry_dimension: int) -> list[str]:
    errors = []
    boundary_dimension = geometry_dimension - 1
    for group in groups:
        expected_dimension = geometry_dimension if group.role == "domain" else boundary_dimension
        if group.dimension != expected_dimension:
            errors.append(
                f"{group.name}: role={group.role}, dimension={group.dimension}, expected={expected_dimension}"
            )
    return errors


def _role_mapping_coverage(config: dict[str, Any]) -> dict[str, Any]:
    role_to_boundary_type = config["downstream_boundary_map"]["role_to_boundary_type"]
    required_roles = set(config["downstream_boundary_map"]["required_roles"])
    declared_roles = {group.role for group in _groups(config)}
    mapped_roles = set(role_to_boundary_type)
    covered_roles = required_roles & declared_roles & mapped_roles
    missing_declared_roles = sorted(required_roles - declared_roles)
    missing_mapped_roles = sorted(required_roles - mapped_roles)
    coverage = len(covered_roles) / len(required_roles) if required_roles else 1.0
    return {
        "required_roles": sorted(required_roles),
        "declared_roles": sorted(declared_roles),
        "mapped_roles": sorted(mapped_roles),
        "covered_roles": sorted(covered_roles),
        "missing_declared_roles": missing_declared_roles,
        "missing_mapped_roles": missing_mapped_roles,
        "coverage": coverage,
    }


def summarize_contract_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    groups = _groups(config)
    name_counts = Counter(group.name for group in groups)
    duplicate_names = sorted(name for name, count in name_counts.items() if count > 1)
    required_names = set(config["validation"]["required_group_names"])
    declared_names = {group.name for group in groups}
    dimension_errors = _dimension_role_errors(groups, int(config["geometry"]["dimension"]))
    role_coverage = _role_mapping_coverage(config)
    result = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "physical_group_count": len(groups),
        "required_group_count": sum(1 for group in groups if group.required),
        "missing_required_group_count": len(required_names - declared_names),
        "duplicate_name_count": len(duplicate_names),
        "dimension_role_error_count": len(dimension_errors),
        "required_role_count": len(role_coverage["required_roles"]),
        "covered_required_role_count": len(role_coverage["covered_roles"]),
        "role_mapping_coverage": role_coverage["coverage"],
    }
    if validation is not None:
        result["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return result


def validate_boundary_contract(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    groups = _groups(config)
    declared_names = {group.name for group in groups}
    required_names = set(config["validation"]["required_group_names"])
    declared_roles = {group.role for group in groups}
    required_roles = set(config["validation"]["required_roles"])
    name_counts = Counter(group.name for group in groups)
    duplicate_names = sorted(name for name, count in name_counts.items() if count > 1)
    dimension_errors = _dimension_role_errors(groups, int(config["geometry"]["dimension"]))
    role_coverage = _role_mapping_coverage(config)

    _check(
        checks,
        "physical_groups.required_names",
        required_names.issubset(declared_names),
        f"groups={sorted(declared_names)}, required={sorted(required_names)}",
    )
    _check(
        checks,
        "physical_groups.required_roles",
        required_roles.issubset(declared_roles),
        f"roles={sorted(declared_roles)}, required={sorted(required_roles)}",
    )
    _check(
        checks,
        "physical_groups.duplicate_names",
        not duplicate_names,
        json.dumps({"duplicates": duplicate_names}, ensure_ascii=False),
    )
    if config["validation"]["require_dimension_role_compatibility"]:
        _check(
            checks,
            "physical_groups.dimension_role",
            not dimension_errors,
            json.dumps({"errors": dimension_errors}, ensure_ascii=False),
        )
    if config["validation"]["require_downstream_role_coverage"]:
        _check(
            checks,
            "downstream_boundary_map.required_role_coverage",
            role_coverage["coverage"] == 1.0,
            json.dumps(role_coverage, ensure_ascii=False),
        )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Gmsh physical group semantic contract; no mesh generation or solver execution",
        "checks": checks,
        "details": {
            "group_names": sorted(declared_names),
            "roles": sorted(declared_roles),
            "duplicate_names": duplicate_names,
            "dimension_role_errors": dimension_errors,
            "role_coverage": role_coverage,
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_boundary_contract(config)
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
        "scope": "Gmsh physical group contract manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
