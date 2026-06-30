"""OpenFOAM runtime execution and log parsing for C04."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_force_metrics, write_y_plus_summary
from .validation import validate_runtime_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
RESIDUAL_RE = re.compile(
    rf"(?:\w+:\s+)?Solving for\s+(?P<field>[\w.]+),\s+Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+No Iterations\s+(?P<iterations>\d+)"
)
CELL_COUNT_RE = re.compile(r"cells:\s+(\d+)")
NON_ORTHO_RE = re.compile(rf"Max\s+non-orthogonality\s+=\s+({FLOAT_RE})")
SKEW_RE = re.compile(rf"Max\s+skewness\s+=\s+({FLOAT_RE})")


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def parse_simplefoam_log(log_text: str) -> dict[str, Any]:
    residual_history = []
    for match in RESIDUAL_RE.finditer(log_text):
        residual_history.append(
            {
                "field": match.group("field"),
                "initial": float(match.group("initial")),
                "final": float(match.group("final")),
                "iterations": int(match.group("iterations")),
            }
        )
    max_final = max((item["final"] for item in residual_history), default=math.nan)
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or "Segmentation fault" in log_text or _true_floating_exception(log_text)
    return {
        "started": "Starting time loop" in log_text or bool(residual_history),
        "fatal_error_detected": fatal,
        "residual_history": residual_history,
        "max_final_residual": max_final,
    }


def parse_mesh_logs(snappy_log: str, check_mesh_log: str) -> dict[str, Any]:
    cell_match = CELL_COUNT_RE.search(check_mesh_log)
    non_ortho_match = NON_ORTHO_RE.search(check_mesh_log)
    skew_match = SKEW_RE.search(check_mesh_log)
    return {
        "snappy_completed": "Finished meshing" in snappy_log or "End" in snappy_log,
        "mesh_ok": "Mesh OK" in check_mesh_log,
        "fatal_error_detected": "FOAM FATAL" in check_mesh_log or "Failed" in check_mesh_log,
        "cell_count": int(cell_match.group(1)) if cell_match else 0,
        "max_non_orthogonality": float(non_ortho_match.group(1)) if non_ortho_match else math.nan,
        "max_skewness": float(skew_match.group(1)) if skew_match else math.nan,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _command_log(runtime: dict[str, Any], token: str, output_dir: Path) -> Path:
    for item in runtime.get("commands", []):
        if token in item.get("command", ""):
            return Path(item["log"])
    return output_dir / "logs" / f"log.{token}"


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    logs = {Path(item["log"]).name: item["log"] for item in runtime.get("commands", [])}
    snappy_log = _command_log(runtime, "snappyHexMesh", output_dir)
    check_mesh_log = _command_log(runtime, "checkMesh", output_dir)
    simplefoam_log = _command_log(runtime, "simpleFoam", output_dir)
    mesh_metrics = parse_mesh_logs(
        snappy_log.read_text(encoding="utf-8") if snappy_log.exists() else "",
        check_mesh_log.read_text(encoding="utf-8") if check_mesh_log.exists() else "",
    )
    solver_metrics = parse_simplefoam_log(simplefoam_log.read_text(encoding="utf-8") if simplefoam_log.exists() else "")
    force_metrics = write_force_metrics(config, output_dir)
    y_plus_metrics = {"available": False, "reason": "yPlus summary extraction is not implemented without runtime yPlus source."}
    return {
        "schema_version": "openfoam_c04_metrics_v1",
        "parser": {
            "name": "openfoam_c04_motorbike_mesh_solver_force_parser",
            "version": 1,
            "limitations": [
                "Static readiness does not execute motorBike. Runtime validation requires native yPlus or an explicitly marked proxy source.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "mesh": mesh_metrics,
        "solver": solver_metrics,
        "postprocess": {"force_coefficients": force_metrics, "y_plus": y_plus_metrics},
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    status = "passed" if validation["passed"] else "failed"
    forces = metrics.get("postprocess", {}).get("force_coefficients", {})
    y_plus = metrics.get("postprocess", {}).get("y_plus", {})
    lines = [
        f"# OpenFOAM C04 {config['case_id']} runtime report",
        "",
        f"- gate: `{validation['gate']}`",
        f"- status: `{status}`",
        f"- runtime profile: `{config['openfoam']['runtime_profile']}`",
        f"- Cd tail mean: `{forces.get('cd_tail_mean')}`",
        f"- Cl tail mean: `{forces.get('cl_tail_mean')}`",
        f"- y+ mean: `{y_plus.get('mean')}`",
        "",
        "## Scope",
        "",
        "This report covers motorBike mesh generation, simpleFoam execution, force coefficient extraction, and y+ validation only when runtime artifacts exist.",
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
