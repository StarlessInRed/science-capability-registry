"""OpenFOAM runtime execution and log parsing for C02."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_analytical_metrics
from .validation import validate_runtime_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
RESIDUAL_RE = re.compile(
    rf"Solving for\s+(?P<field>[\w.]+),\s+Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+No Iterations\s+(?P<iterations>\d+)"
)


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def parse_potentialfoam_log(log_text: str) -> dict[str, Any]:
    residual_history = []
    last_residuals: dict[str, dict[str, Any]] = {}
    for match in RESIDUAL_RE.finditer(log_text):
        item = {
            "field": match.group("field"),
            "initial": float(match.group("initial")),
            "final": float(match.group("final")),
            "iterations": int(match.group("iterations")),
        }
        residual_history.append(item)
        last_residuals[item["field"]] = {
            "initial": item["initial"],
            "final": item["final"],
            "iterations": item["iterations"],
        }
    fatal = (
        "FOAM FATAL" in log_text
        or "FOAM exiting" in log_text
        or "Segmentation fault" in log_text
        or "sigFpe::sigHandler" in log_text
        or _true_floating_exception(log_text)
    )
    started = "potentialFoam" in log_text or "Reading field" in log_text or bool(residual_history)
    return {
        "started": started,
        "fatal_error_detected": fatal,
        "residual_history": residual_history,
        "last_residuals": last_residuals,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _solver_log(runtime: dict[str, Any], output_dir: Path) -> Path:
    for item in runtime.get("commands", []):
        if "potentialFoam" in item.get("command", ""):
            return Path(item["log"])
    return output_dir / "logs" / "log.potentialFoam"


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    log_path = _solver_log(runtime, output_dir)
    solver_metrics = parse_potentialfoam_log(log_path.read_text(encoding="utf-8") if log_path.exists() else "")
    analytical_metrics = {}
    try:
        analytical_metrics = write_analytical_metrics(config, output_dir)
    except (FileNotFoundError, ValueError, IndexError, ZeroDivisionError) as exc:
        analytical_metrics = {"available": False, "reason": str(exc)}
    logs = {Path(item["log"]).name: item["log"] for item in runtime.get("commands", [])}
    return {
        "schema_version": "openfoam_c02_metrics_v1",
        "parser": {
            "name": "openfoam_c02_potentialfoam_analytical_parser",
            "version": 1,
            "limitations": [
                "Analytical comparison uses cell-centre and cylinder owner-cell samples; boundary and finite-domain effects are reported through configured tolerances.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "solver": solver_metrics,
        "postprocess": {"analytical": analytical_metrics},
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    analytical = metrics.get("postprocess", {}).get("analytical", {})
    field = analytical.get("field", {})
    cp = analytical.get("surface_cp", {})
    strategy = config["postprocess"]["sample_policy"]["finite_domain_error_strategy"]
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# OpenFOAM C02 {config['case_id']} runtime report",
        "",
        f"- gate: `{validation['gate']}`",
        f"- status: `{status}`",
        f"- runtime profile: `{config['openfoam']['runtime_profile']}`",
        f"- velocity L2 error: `{field.get('velocity_l2_error')}`",
        f"- pressure L2 error: `{field.get('pressure_l2_error')}`",
        f"- Cp Linf error: `{cp.get('cp_linf_error')}`",
        f"- finite-domain strategy: `{strategy}`",
        "",
        "## Scope",
        "",
        "This report covers local potentialFoam execution and Python analytical comparison against cylinder potential-flow formulas."
        if strategy == "unbounded_analytic_solution_with_masked_sampling"
        else "This report covers local potentialFoam execution and diagnostic finite-error extraction only; a finite-domain corrected reference is required before analytical validation.",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime_outputs(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    metrics = build_runtime_metrics(config, output_dir, runtime)
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_runtime_metrics(metrics, config, output_dir)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_runtime_report(config, metrics, validation, output_dir)
    return {"metrics": metrics, "validation": validation, "metrics_path": metrics_path, "validation_path": validation_path}
