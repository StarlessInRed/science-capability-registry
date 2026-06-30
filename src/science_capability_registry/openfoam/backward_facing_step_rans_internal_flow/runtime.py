"""OpenFOAM runtime execution and log parsing for C03."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_flow_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
RESIDUAL_RE = re.compile(
    rf"(?:\w+:\s+)?Solving for\s+(?P<field>[\w.]+),\s+"
    rf"Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+"
    r"No Iterations\s+(?P<iterations>\d+)"
)
CONTINUITY_RE = re.compile(
    rf"time step continuity errors\s*:\s*sum local =\s*(?P<local>{FLOAT_RE}),\s+"
    rf"global =\s*(?P<global>{FLOAT_RE}),\s+cumulative =\s*(?P<cumulative>{FLOAT_RE})"
)
TIME_RE = re.compile(rf"^Time =\s*({FLOAT_RE})", re.MULTILINE)
CHECK_MESH_OK_RE = re.compile(r"Mesh OK", re.IGNORECASE)


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def parse_simplefoam_log(log_text: str) -> dict[str, Any]:
    times = [float(match.group(1)) for match in TIME_RE.finditer(log_text)]
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
        last_residuals[item["field"]] = {"initial": item["initial"], "final": item["final"], "iterations": item["iterations"]}
    continuity_history = [
        {
            "sum_local": float(match.group("local")),
            "global": float(match.group("global")),
            "cumulative": float(match.group("cumulative")),
        }
        for match in CONTINUITY_RE.finditer(log_text)
    ]
    floating_exception = any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or floating_exception
    return {
        "started": "Starting time loop" in log_text,
        "fatal_error_detected": fatal,
        "times": times,
        "final_time": times[-1] if times else None,
        "iteration_count": len(times),
        "residual_history": residual_history,
        "last_residuals": last_residuals,
        "continuity_history": continuity_history,
        "last_continuity": continuity_history[-1] if continuity_history else None,
    }


def parse_check_mesh_log(log_text: str) -> dict[str, Any]:
    return {
        "ran": bool(log_text.strip()),
        "mesh_ok": bool(CHECK_MESH_OK_RE.search(log_text)),
        "fatal_error_detected": "FOAM FATAL" in log_text or "Failed" in log_text,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    logs = {Path(item["log"]).name: item["log"] for item in runtime["commands"]}
    solver_log = output_dir / "logs" / "log.simpleFoam"
    check_mesh_log = output_dir / "logs" / "log.checkMesh"
    solver_metrics = parse_simplefoam_log(solver_log.read_text(encoding="utf-8") if solver_log.exists() else "")
    check_mesh_metrics = parse_check_mesh_log(check_mesh_log.read_text(encoding="utf-8") if check_mesh_log.exists() else "")
    postprocess_metrics = write_flow_metrics(config, output_dir) if solver_metrics.get("final_time") is not None else {}
    time_dirs = []
    for path in (output_dir / "case").iterdir():
        if path.is_dir():
            try:
                value = float(path.name)
            except ValueError:
                continue
            time_dirs.append({"name": path.name, "time": value})
    time_dirs.sort(key=lambda item: item["time"])
    return {
        "schema_version": "openfoam_c03_metrics_v1",
        "parser": {
            "name": "openfoam_c03_log_and_field_parser",
            "version": 1,
            "limitations": [
                "OpenFOAM functionObjects are not used because this local OpenFOAM.com v2112 WSL profile emits sha1 IO errors, including ext4 probe paths.",
                "Wall shear and yPlus are Python near-wall proxy metrics, not OpenFOAM wallShearStress/yPlus functionObject output.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "mesh": check_mesh_metrics,
        "solver": solver_metrics,
        "postprocess": postprocess_metrics,
        "artifacts": {
            "logs": logs,
            "time_directories": time_dirs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    commands = metrics["runtime"].get("commands", [])
    for command in config["solver"]["command_sequence"]:
        match = next((item for item in commands if item["command"] == command), None)
        check(f"command.{command}.returncode", bool(match and match["returncode"] == 0), json.dumps(match or {}, ensure_ascii=False))
    mesh_metrics = metrics.get("mesh", {})
    check("mesh.checkMesh_ok", mesh_metrics.get("mesh_ok") is True, json.dumps(mesh_metrics, ensure_ascii=False))
    solver = metrics.get("solver", {})
    end_time = float(config["numerics"]["control"]["end_time_iterations"])
    final_time = solver.get("final_time")
    check("solver.started", solver.get("started") is True, "Starting time loop found")
    check("solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    check("solver.final_time", _is_finite(final_time) and float(final_time) >= end_time - 1e-12, f"final_time={final_time}, expected={end_time}")
    residual_values = [item.get("final") for item in solver.get("last_residuals", {}).values()]
    max_final = max((float(value) for value in residual_values if _is_finite(value)), default=float("inf"))
    threshold = float(config["validation"]["max_final_residual"])
    check("solver.final_residual_threshold", math.isfinite(max_final) and max_final <= threshold, f"max_final_residual={max_final}, threshold={threshold}")
    last_continuity = solver.get("last_continuity") or {}
    continuity_limit = float(config["validation"]["max_continuity_sum_local"])
    check(
        "solver.continuity_sum_local",
        bool(last_continuity) and _is_finite(last_continuity.get("sum_local")) and abs(float(last_continuity["sum_local"])) <= continuity_limit,
        json.dumps(last_continuity, ensure_ascii=False),
    )
    post = metrics.get("postprocess", {})
    pressure_drop = post.get("pressure", {}).get("pressure_drop_kinematic_m2_s2")
    check("postprocess.pressure_drop_positive", _is_finite(pressure_drop) and float(pressure_drop) > 0.0, str(pressure_drop))
    wall = post.get("wall", {})
    check("postprocess.lower_wall_shear_samples", int(wall.get("sample_count", 0)) >= 5, json.dumps(wall, ensure_ascii=False))
    field_stats = post.get("field_stats", {})
    check("postprocess.velocity_finite", field_stats.get("velocity_finite") is True, json.dumps(field_stats, ensure_ascii=False))
    for rel_path in config["validation"]["required_generated_files"]:
        path = output_dir / rel_path
        check(f"artifact.generated.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        check(f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local WSL OpenFOAM C03 runtime with Python field postprocess and integration-ready metrics",
        "checks": checks,
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    status = "passed" if validation["passed"] else "failed"
    solver = metrics["solver"]
    post = metrics.get("postprocess", {})
    lines = [
        f"# OpenFOAM C03 {config['case_id']} runtime report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime profile: {config['openfoam']['runtime_profile']}",
        f"- final pseudo-time: {solver.get('final_time')}",
        f"- pressure drop: {post.get('pressure', {}).get('pressure_drop_kinematic_m2_s2')}",
        f"- reattachment proxy x/H: {post.get('wall', {}).get('reattachment_length_over_H')}",
        "",
        "## Artifacts",
        "",
        "- manifest.json",
        "- metrics.json",
        "- validation.json",
        "- logs/log.blockMesh",
        "- logs/log.checkMesh",
        "- logs/log.simpleFoam",
        "- postprocess/velocity_profiles.csv",
        "- postprocess/lower_wall_shear.csv",
        "- postprocess/pressure_coefficient.csv",
        "- postprocess/yplus_summary.csv",
        "",
        "## Scope",
        "",
        "This report validates one local OpenFOAM.com v2112 WSL case. Wall shear and yPlus values are Python near-wall proxy metrics because OpenFOAM functionObjects fail with sha1 IO errors in this local profile, including ext4 probe paths.",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
