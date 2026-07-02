"""Validation helpers for COMSOL C02 model construction."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


def load_json_artifact(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return data


def summarize_environment_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    required = [item for item in checks if item["required"]]
    optional = [item for item in checks if not item["required"]]
    return {
        "required_count": len(required),
        "required_configured_count": sum(1 for item in required if item["configured"]),
        "required_existing_count": sum(1 for item in required if item["exists"]),
        "optional_count": len(optional),
        "optional_configured_count": sum(1 for item in optional if item["configured"]),
        "all_required_configured": all(item["configured"] for item in required),
        "all_required_paths_exist": all(item["exists"] for item in required),
    }


def configured_required_tags(config: dict[str, Any]) -> dict[str, str]:
    tags = config["model_tree"]["tags"]
    return {name: str(tags[name]) for name in config["validation"]["required_tags"]}


def duplicate_tag_count(config: dict[str, Any]) -> int:
    tag_values = list(configured_required_tags(config).values())
    counts = Counter(tag_values)
    return sum(1 for count in counts.values() if count > 1)


def missing_required_tags(config: dict[str, Any], manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return list(config["validation"]["required_tags"])
    declared = manifest.get("declared_tags", {})
    if not isinstance(declared, dict):
        return list(config["validation"]["required_tags"])
    missing = []
    for key, expected in configured_required_tags(config).items():
        if declared.get(key) != expected:
            missing.append(key)
    return missing


def finite_parameter_count(config: dict[str, Any], manifest: dict[str, Any] | None) -> int:
    if manifest is None:
        return 0
    parameter_values = manifest.get("parameter_values", {})
    if not isinstance(parameter_values, dict):
        return 0
    finite_count = 0
    for parameter in config["model_tree"]["parameters"]:
        value = parameter_values.get(parameter["name"])
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            finite_count += 1
    return finite_count


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
    check_artifacts: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    backend_type = config["backend"]["type"]
    env_summary = metrics["environment_summary"]
    add_check("config.validated", bool(metrics["validated_config"]), "configuration schema accepted")
    add_check("script.generated", bool(metrics["script_generated"]), metrics["script_file"])
    add_check("model_tags.unique", metrics["duplicate_tag_count"] == 0, str(metrics["duplicate_tag_count"]))
    add_check("model_tags.required_present", metrics["required_tag_missing_count"] == 0, json.dumps(metrics["missing_required_tags"]))
    add_check("solver.not_executed", metrics["solver_executed"] is False, str(metrics["solver_executed"]))

    if backend_type == "dry_run_only" or metrics["runtime_status"] == "dry_run_not_executed":
        scope = "COMSOL C02 dry-run model construction script contract; no MATLAB or COMSOL execution"
        gate = "static-readiness"
    else:
        add_check(
            "environment.required_configured",
            bool(env_summary["all_required_configured"]),
            f"{env_summary['required_configured_count']} of {env_summary['required_count']}",
        )
        if config["validation"]["require_path_exists"]:
            add_check(
                "environment.required_paths_exist",
                bool(env_summary["all_required_paths_exist"]),
                f"{env_summary['required_existing_count']} of {env_summary['required_count']}",
            )
        scope = "COMSOL C02 MATLAB/LiveLink model-construction preflight; no COMSOL solver execution"
        gate = config["validation"]["gate"]

    if config["validation"]["require_matlab_execution"] and metrics["runtime_status"] != "dry_run_not_executed":
        add_check("matlab.return_code", metrics.get("matlab_return_code") == 0, str(metrics.get("matlab_return_code")))
        add_check("matlab.model_tree_manifest", bool(metrics["model_tree_manifest_written"]), "model_tree_manifest.json")
        add_check("matlab.construction_manifest", bool(metrics["construction_manifest_written"]), "construction_manifest.json")
        add_check(
            "matlab.parameters_finite",
            metrics["finite_parameter_count"] == metrics["parameter_count"],
            f"{metrics['finite_parameter_count']} of {metrics['parameter_count']}",
        )
        scope = "COMSOL C02 MATLAB/LiveLink model tree construction smoke"
        gate = "smoke"

    if check_artifacts:
        artifact_targets = config["validation"]["required_artifacts"]
        if metrics["runtime_status"] == "dry_run_not_executed":
            artifact_targets = [
                config["model_tree"]["script_filename"],
                "manifest.json",
                "metrics.json",
                "validation.json",
                "validation_report.md",
            ]
        for rel_path in artifact_targets:
            path = output_dir / rel_path
            add_check(f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": gate,
        "scope": scope,
        "checks": checks,
        "details": {
            "runtime_status": metrics["runtime_status"],
            "no_claims": config["validation"]["no_claims"],
        },
    }
