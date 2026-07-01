"""OpenFOAM runtime execution and log parsing for C06."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_vof_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TIME_RE = re.compile(rf"^Time =\s*({FLOAT_RE})", re.MULTILINE)
COURANT_RE = re.compile(rf"Courant Number mean:\s*({FLOAT_RE})\s+max:\s*({FLOAT_RE})")
ALPHA_COURANT_RE = re.compile(rf"Interface Courant Number mean:\s*({FLOAT_RE})\s+max:\s*({FLOAT_RE})")
RESIDUAL_RE = re.compile(rf"Solving for\s+(?P<field>[\w.]+),\s+Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+Final residual =\s*(?P<final>{FLOAT_RE}),\s+No Iterations\s+(?P<iterations>\d+)")
CONTINUITY_RE = re.compile(rf"time step continuity errors\s*:\s*sum local =\s*(?P<local>{FLOAT_RE}),\s+global =\s*(?P<global>{FLOAT_RE}),\s+cumulative =\s*(?P<cumulative>{FLOAT_RE})")
ALPHA_BOUNDS_RE = re.compile(rf"Phase-1 volume fraction =\s*({FLOAT_RE})\s+Min\(alpha.water\) =\s*({FLOAT_RE})\s+Max\(alpha.water\) =\s*({FLOAT_RE})")
CHECK_MESH_OK_RE = re.compile(r"Mesh OK", re.IGNORECASE)


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def parse_interfoam_log(log_text: str) -> dict[str, Any]:
    times = [float(match.group(1)) for match in TIME_RE.finditer(log_text)]
    courant_history = [{"mean": float(match.group(1)), "max": float(match.group(2))} for match in COURANT_RE.finditer(log_text)]
    alpha_courant_history = [{"mean": float(match.group(1)), "max": float(match.group(2))} for match in ALPHA_COURANT_RE.finditer(log_text)]
    residual_history = []
    last_residuals: dict[str, dict[str, Any]] = {}
    for match in RESIDUAL_RE.finditer(log_text):
        item = {"field": match.group("field"), "initial": float(match.group("initial")), "final": float(match.group("final")), "iterations": int(match.group("iterations"))}
        residual_history.append(item)
        last_residuals[item["field"]] = {"initial": item["initial"], "final": item["final"], "iterations": item["iterations"]}
    continuity_history = [{"sum_local": float(match.group("local")), "global": float(match.group("global")), "cumulative": float(match.group("cumulative"))} for match in CONTINUITY_RE.finditer(log_text)]
    alpha_bounds_history = [{"volume_fraction": float(match.group(1)), "min": float(match.group(2)), "max": float(match.group(3))} for match in ALPHA_BOUNDS_RE.finditer(log_text)]
    floating_exception = any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or floating_exception
    return {
        "started": "Starting time loop" in log_text,
        "fatal_error_detected": fatal,
        "times": times,
        "final_time": times[-1] if times else None,
        "time_step_count": len(times),
        "courant_history": courant_history,
        "alpha_courant_history": alpha_courant_history,
        "max_courant_number": max((entry["max"] for entry in courant_history), default=None),
        "max_alpha_courant_number": max((entry["max"] for entry in alpha_courant_history), default=None),
        "residual_history": residual_history,
        "last_residuals": last_residuals,
        "continuity_history": continuity_history,
        "last_continuity": continuity_history[-1] if continuity_history else None,
        "alpha_bounds_history": alpha_bounds_history,
        "last_alpha_bounds": alpha_bounds_history[-1] if alpha_bounds_history else None,
    }


def parse_check_mesh_log(log_text: str) -> dict[str, Any]:
    return {"ran": bool(log_text.strip()), "mesh_ok": bool(CHECK_MESH_OK_RE.search(log_text)), "fatal_error_detected": "FOAM FATAL" in log_text or "Failed" in log_text}


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _runtime_log_path(runtime: dict[str, Any], command: str, output_dir: Path) -> Path:
    match = next(
        (item for item in runtime.get("commands", []) if item.get("command") == command),
        None,
    )
    if match and match.get("log"):
        return Path(match["log"])
    return output_dir / "logs" / f"log.{command.split()[0]}"


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    logs = {Path(item["log"]).name: item["log"] for item in runtime["commands"]}
    solver_log = _runtime_log_path(runtime, "interFoam", output_dir)
    check_mesh_log = _runtime_log_path(runtime, "checkMesh", output_dir)
    solver_metrics = parse_interfoam_log(solver_log.read_text(encoding="utf-8") if solver_log.exists() else "")
    check_mesh_metrics = parse_check_mesh_log(check_mesh_log.read_text(encoding="utf-8") if check_mesh_log.exists() else "")
    postprocess_metrics = write_vof_metrics(config, output_dir) if solver_metrics.get("final_time") is not None else {}
    return {
        "schema_version": "openfoam_c06_metrics_v1",
        "parser": {"name": "openfoam_c06_log_and_alpha_parser", "version": 1, "limitations": ["OpenFOAM sampling functionObject is disabled because this local OpenFOAM.com v2112 WSL profile emits sha1 IO errors, including ext4 probe paths."]},
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "mesh": check_mesh_metrics,
        "solver": solver_metrics,
        "postprocess": postprocess_metrics,
        "artifacts": {"logs": logs, "metrics_json": str(output_dir / "metrics.json"), "validation_json": str(output_dir / "validation.json"), "validation_report": str(output_dir / "validation_report.md")},
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
    end_time = float(config["numerics"]["control"]["end_time_s"])
    final_time = solver.get("final_time")
    check("solver.started", solver.get("started") is True, "Starting time loop found")
    check("solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    check("solver.final_time", _is_finite(final_time) and float(final_time) >= end_time - 1e-12, f"final_time={final_time}, expected={end_time}")
    max_co = solver.get("max_courant_number")
    max_alpha_co = solver.get("max_alpha_courant_number")
    check("solver.max_courant", _is_finite(max_co) and float(max_co) <= float(config["validation"]["max_courant_number"]), str(max_co))
    check("solver.max_alpha_courant", _is_finite(max_alpha_co) and float(max_alpha_co) <= float(config["validation"]["max_alpha_courant_number"]), str(max_alpha_co))
    post = metrics.get("postprocess", {})
    bounds = post.get("alpha_bounds", {})
    check("alpha.finite", post.get("alpha_finite") is True, json.dumps(bounds, ensure_ascii=False))
    check("alpha.lower_bound", _is_finite(bounds.get("alpha_min")) and float(bounds["alpha_min"]) >= float(config["validation"]["alpha_min_tolerance"]), json.dumps(bounds, ensure_ascii=False))
    check("alpha.upper_bound", _is_finite(bounds.get("alpha_max")) and float(bounds["alpha_max"]) <= 1.0 + float(config["validation"]["alpha_max_tolerance"]), json.dumps(bounds, ensure_ascii=False))
    volume = post.get("volume", {})
    check("volume.relative_error", _is_finite(volume.get("relative_error")) and abs(float(volume["relative_error"])) <= float(config["validation"]["max_water_volume_relative_error"]), json.dumps(volume, ensure_ascii=False))
    front = post.get("front", {})
    check("front.position_finite", _is_finite(front.get("front_x_m")) and float(front["front_x_m"]) > 0.0, json.dumps(front, ensure_ascii=False))
    for rel_path in config["validation"]["required_generated_files"]:
        path = output_dir / rel_path
        check(f"artifact.generated.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        if rel_path == "logs/log.blockMesh":
            path = _runtime_log_path(metrics["runtime"], "blockMesh", output_dir)
        elif rel_path == "logs/log.setFields":
            path = _runtime_log_path(metrics["runtime"], "setFields", output_dir)
        elif rel_path == "logs/log.checkMesh":
            path = _runtime_log_path(metrics["runtime"], "checkMesh", output_dir)
        elif rel_path == "logs/log.interFoam":
            path = _runtime_log_path(metrics["runtime"], "interFoam", output_dir)
        check(f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    return {"passed": all(item["passed"] for item in checks), "gate": config["validation"]["gate"], "scope": "local WSL OpenFOAM C06 runtime with Python alpha-field postprocess", "checks": checks}


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    status = "passed" if validation["passed"] else "failed"
    solver = metrics["solver"]
    post = metrics.get("postprocess", {})
    logs = metrics.get("artifacts", {}).get("logs", {})
    lines = [
        f"# OpenFOAM C06 {config['case_id']} runtime report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- runtime profile: {config['openfoam']['runtime_profile']}",
        f"- final time: {solver.get('final_time')}",
        f"- max Courant: {solver.get('max_courant_number')}",
        f"- max alpha Courant: {solver.get('max_alpha_courant_number')}",
        f"- final front x: {post.get('front', {}).get('front_x_m')}",
        f"- water volume relative error: {post.get('volume', {}).get('relative_error')}",
        f"- blockMesh log: {logs.get('log.01_blockMesh', logs.get('log.blockMesh', ''))}",
        f"- setFields log: {logs.get('log.02_setFields', logs.get('log.setFields', ''))}",
        f"- checkMesh log: {logs.get('log.03_checkMesh', logs.get('log.checkMesh', ''))}",
        f"- interFoam log: {logs.get('log.04_interFoam', logs.get('log.interFoam', ''))}",
        "",
        "## Scope",
        "",
        "This report validates one local OpenFOAM.com v2112 WSL dam-break case with Python alpha-field postprocess. It is not an external experimental validation.",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
