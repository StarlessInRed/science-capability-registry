"""Validation for Fluent C01-C08 seed-suite static readiness."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple

from .config import repo_relative_path


class SeedCase(NamedTuple):
    seed_id: str
    asset_path: str
    capability_slug: str
    benchmark_status: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SeedCase":
        return cls(
            seed_id=str(data["seed_id"]),
            asset_path=str(data["asset_path"]),
            capability_slug=str(data["capability_slug"]),
            benchmark_status=str(data["benchmark_status"]),
        )


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _seed_cases(config: dict[str, Any]) -> list[SeedCase]:
    return [SeedCase.from_mapping(item) for item in config["seed_cases"]]


def _contains_local_drive_path(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.replace("/", "\\")
        return len(normalized) >= 3 and normalized[1:3] == ":\\"
    if isinstance(value, dict):
        return any(_contains_local_drive_path(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_local_drive_path(item) for item in value)
    return False


def summarize_seed_metrics(config: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    seeds = _seed_cases(config)
    required_ids = set(config["validation"]["required_seed_ids"])
    declared_ids = {seed.seed_id for seed in seeds}
    modes = set(config["learning_loop"]["required_modes"])
    metrics = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "seed_count": len(seeds),
        "required_seed_count": len(required_ids),
        "missing_seed_count": len(required_ids - declared_ids),
        "extra_seed_count": len(declared_ids - required_ids),
        "benchmark_candidate_count": sum(1 for seed in seeds if seed.benchmark_status == "benchmark_candidate"),
        "mode_count": len(modes),
        "mismatch_class_count": len(config["learning_loop"]["mismatch_classes"]),
    }
    if validation is not None:
        metrics["validation"] = {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        }
    return metrics


def validate_seed_suite(config: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    seeds = _seed_cases(config)
    required_ids = set(config["validation"]["required_seed_ids"])
    declared_ids = {seed.seed_id for seed in seeds}
    seed_counts = Counter(seed.seed_id for seed in seeds)
    duplicate_ids = sorted(seed_id for seed_id, count in seed_counts.items() if count > 1)
    required_modes = set(config["validation"]["required_modes"])
    declared_modes = set(config["learning_loop"]["required_modes"])

    _check(checks, "seed_cases.exact_count", len(seeds) == 8, f"seed_count={len(seeds)}")
    _check(
        checks,
        "seed_cases.required_ids",
        declared_ids == required_ids,
        f"declared={sorted(declared_ids)}, required={sorted(required_ids)}",
    )
    _check(checks, "seed_cases.unique_ids", not duplicate_ids, f"duplicates={duplicate_ids}")
    allowed_statuses = {"benchmark_candidate", "package_skeleton_created"}
    _check(
        checks,
        "seed_cases.benchmark_status",
        all(seed.benchmark_status in allowed_statuses for seed in seeds),
        f"allowed={sorted(allowed_statuses)}",
    )
    _check(
        checks,
        "learning_loop.required_modes",
        required_modes.issubset(declared_modes),
        f"declared={sorted(declared_modes)}, required={sorted(required_modes)}",
    )
    for seed in seeds:
        asset_path = repo_relative_path(seed.asset_path)
        _check(checks, f"asset.exists.{seed.seed_id}", asset_path.exists(), seed.asset_path)
    profile_path = repo_relative_path(config["fluent"]["runtime_profile_config"])
    _check(checks, "runtime_profile.exists", profile_path.exists(), str(profile_path))
    _check(
        checks,
        "paths.no_local_drive_paths",
        not _contains_local_drive_path({key: value for key, value in config.items() if key != "_config_path"}),
        "config must use logical or repo-relative paths",
    )

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C01-C08 seed-suite static contract; no Fluent solver invocation",
        "checks": checks,
        "details": {
            "seed_ids": sorted(declared_ids),
            "required_modes": sorted(declared_modes),
            "mismatch_classes": config["learning_loop"]["mismatch_classes"],
        },
    }


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    validation = validate_seed_suite(config)
    checks = list(validation["checks"])
    _check(checks, "manifest.validated_config", manifest.get("validated_config") is True, "validated_config=true")
    for section in ["capability_id", "case_id", "schema_id", "fluent", "learning_loop", "seed_cases", "generated_files"]:
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
        "scope": "Fluent seed-suite manifest and artifact completeness",
        "checks": checks,
        "details": validation["details"],
    }
