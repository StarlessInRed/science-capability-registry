"""OpenFOAM runtime execution and log parsing for C05."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_force_metrics
from .validation import validate_runtime_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TIME_RE = re.compile(rf"^Time =\s*({FLOAT_RE})", re.MULTILINE)
COURANT_RE = re.compile(rf"Courant Number mean:\s*({FLOAT_RE})\s+max:\s*({FLOAT_RE})")
RESIDUAL_RE = re.compile(
    rf"Solving for\s+(?P<field>[\w.]+),\s+Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+No Iterations\s+(?P<iterations>\d+)"
)
CONTINUITY_RE = re.compile(
    rf"time step continuity errors\s*:\s*sum local =\s*(?P<local>{FLOAT_RE}),\s+"
    rf"global =\s*(?P<global>{FLOAT_RE}),\s+cumulative =\s*(?P<cumulative>{FLOAT_RE})"
)


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def parse_pimplefoam_log(log_text: str) -> dict[str, Any]:
    times = [float(match.group(1)) for match in TIME_RE.finditer(log_text)]
    courant_history = [{"mean": float(match.group(1)), "max": float(match.group(2))} for match in COURANT_RE.finditer(log_text)]
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
    continuity_history = [
        {
            "sum_local": float(match.group("local")),
            "global": float(match.group("global")),
            "cumulative": float(match.group("cumulative")),
        }
        for match in CONTINUITY_RE.finditer(log_text)
    ]
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or "Segmentation fault" in log_text or _true_floating_exception(log_text)
    return {
        "started": bool(times or residual_history or "Starting time loop" in log_text),
        "fatal_error_detected": fatal,
        "times": times,
        "final_time": times[-1] if times else None,
        "time_step_count": len(times),
        "courant_history": courant_history,
        "max_courant_number": max((entry["max"] for entry in courant_history), default=None),
        "residual_history": residual_history,
        "last_residuals": last_residuals,
        "continuity_history": continuity_history,
        "last_continuity": continuity_history[-1] if continuity_history else None,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _solver_log(runtime: dict[str, Any], output_dir: Path) -> Path:
    for item in runtime.get("commands", []):
        if "pimpleFoam" in item.get("command", ""):
            return Path(item["log"])
    return output_dir / "logs" / "log.pimpleFoam"


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    log_path = _solver_log(runtime, output_dir)
    solver_metrics = parse_pimplefoam_log(log_path.read_text(encoding="utf-8") if log_path.exists() else "")
    postprocess_metrics = write_force_metrics(config, output_dir) if solver_metrics.get("final_time") is not None else {}
    logs = {Path(item["log"]).name: item["log"] for item in runtime.get("commands", [])}
    return {
        "schema_version": "openfoam_c05_metrics_v1",
        "parser": {
            "name": "openfoam_c05_pimplefoam_force_parser",
            "version": 1,
            "limitations": [
                "Strouhal is computed only from detected lift peaks in coefficient.dat and remains provisional without mesh/time-step sensitivity.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "solver": solver_metrics,
        "postprocess": postprocess_metrics,
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    solver = metrics.get("solver", {})
    strouhal = metrics.get("postprocess", {}).get("strouhal", {})
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# OpenFOAM C05 {config['case_id']} runtime report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- runtime profile: {config['openfoam']['runtime_profile']}",
        f"- final time: {solver.get('final_time')}",
        f"- max Courant: {solver.get('max_courant_number')}",
        f"- Strouhal available: {strouhal.get('available')}",
        f"- Strouhal number: {strouhal.get('strouhal_number')}",
        "",
        "## Scope",
        "",
        "This report validates local OpenFOAM command wiring and force-coefficient artifact extraction. It is not a benchmark-grade shedding-frequency validation.",
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
