"""Validation helpers for COMSOL C01."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def parse_scalar_file(path: Path, scalar_name: str) -> float | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        prefix = f"{scalar_name}="
        if not line.startswith(prefix):
            continue
        try:
            value = float(line[len(prefix) :])
        except ValueError:
            return None
        return value if math.isfinite(value) else None
    return None


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

    if backend_type == "dry_run_only" or metrics["runtime_status"] == "dry_run_not_executed":
        scope = "COMSOL C01 dry-run script contract; no MATLAB or COMSOL execution"
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
        scope = "COMSOL C01 MATLAB/LiveLink preflight; no COMSOL solver execution"
        gate = config["validation"]["gate"]

    if config["validation"]["require_matlab_execution"]:
        add_check("matlab.return_code", metrics.get("matlab_return_code") == 0, str(metrics.get("matlab_return_code")))
        add_check("matlab.scalar_file", bool(metrics["scalar_file_written"]), metrics["scalar_file"])
        add_check("matlab.scalar_finite", metrics["finite_scalar"] is not None, str(metrics["finite_scalar"]))
        scope = "COMSOL C01 MATLAB/LiveLink runtime smoke"
        gate = "smoke"

    if check_artifacts:
        for rel_path in config["validation"]["required_artifacts"]:
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
