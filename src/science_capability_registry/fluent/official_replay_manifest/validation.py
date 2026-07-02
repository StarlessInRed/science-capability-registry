"""Validation for Fluent official replay source manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bindings import binding_errors


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_manifest_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    packages = manifest["packages"]
    kind_totals: dict[str, int] = {}
    entrypoint_totals: dict[str, int] = {}
    missing_expected_count = 0
    for package in packages:
        for kind, count in package["summary"]["entry_kind_counts"].items():
            kind_totals[kind] = kind_totals.get(kind, 0) + int(count)
        entrypoint = package["summary"]["entrypoint_class"]
        entrypoint_totals[entrypoint] = entrypoint_totals.get(entrypoint, 0) + 1
        missing_expected_count += len(package["missing_expected_entry_classes"])
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "package_count": len(packages),
        "readable_package_count": sum(1 for package in packages if package["archive_status"] == "readable"),
        "source_entry_count": len(manifest["entries"]),
        "entry_kind_totals": kind_totals,
        "entrypoint_class_totals": entrypoint_totals,
        "binding_count": len(manifest["capability_bindings"]),
        "missing_expected_entry_class_count": missing_expected_count,
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    metrics = summarize_manifest_metrics(manifest)
    errors = binding_errors(config)
    required_seed_ids = set(config["validation"]["required_seed_ids"])
    bound_seed_ids = {binding["seed_id"] for binding in manifest["capability_bindings"]}

    _check(checks, "bindings.valid", not errors, "; ".join(errors))
    _check(checks, "bindings.required_seed_ids", required_seed_ids == bound_seed_ids, str(sorted(bound_seed_ids)))
    _check(
        checks,
        "packages.readable",
        metrics["readable_package_count"] == metrics["package_count"],
        f"{metrics['readable_package_count']} / {metrics['package_count']}",
    )
    _check(
        checks,
        "packages.expected_entry_classes",
        metrics["missing_expected_entry_class_count"] == 0,
        str(metrics["missing_expected_entry_class_count"]),
    )
    for entry_class in config["validation"]["required_entry_classes"]:
        _check(
            checks,
            f"entries.class.{entry_class}",
            metrics["entry_kind_totals"].get(entry_class, 0) > 0,
            str(metrics["entry_kind_totals"].get(entry_class, 0)),
        )
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
        "scope": "Fluent official replay manifest static-readiness; no Fluent or Workbench execution",
        "checks": checks,
        "details": {
            "metrics": metrics,
            "no_claims": config["validation"]["no_claims"],
        },
    }
