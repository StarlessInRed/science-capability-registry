"""OpenFOAM runtime execution and log parsing for C01."""

from __future__ import annotations

import json
import math
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import write_centerline_profiles

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
COURANT_RE = re.compile(
    rf"Courant Number mean:\s*({FLOAT_RE})\s+max:\s*({FLOAT_RE})"
)
RESIDUAL_RE = re.compile(
    rf"(?:\w+:\s+)?Solving for\s+(?P<field>\w+),\s+"
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


def _float(value: str) -> float:
    return float(value)


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _run_wsl(
    distro: str,
    script: str,
    timeout_s: float,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", distro, "--", "bash", "-lc", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )


def _wsl_path(path: Path, distro: str, timeout_s: float) -> str:
    result = subprocess.run(
        ["wsl", "-d", distro, "--", "wslpath", "-a", path.resolve().as_posix()],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(
            "Failed to map Windows path to WSL path: "
            + (result.stderr.strip() or result.stdout.strip())
        )
    return result.stdout.strip().splitlines()[0]


def _profile_env(distro: str, bashrc_path: str, timeout_s: float) -> dict[str, str]:
    script = (
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
        "printenv WM_PROJECT_VERSION; printenv WM_PROJECT_DIR; "
        "printenv FOAM_TUTORIALS; printenv FOAM_APPBIN; printenv FOAM_USER_APPBIN"
    )
    result = _run_wsl(distro, script, timeout_s)
    lines = result.stdout.splitlines()
    keys = [
        "WM_PROJECT_VERSION",
        "WM_PROJECT_DIR",
        "FOAM_TUTORIALS",
        "FOAM_APPBIN",
        "FOAM_USER_APPBIN",
    ]
    return {key: lines[index] if index < len(lines) else "" for index, key in enumerate(keys)}


def _command_log_name(command: str) -> str:
    executable = command.split()[0]
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", executable)
    return f"log.{safe}"


def _run_openfoam_command(
    distro: str,
    bashrc_path: str,
    case_dir_linux: str,
    command: str,
    timeout_s: float,
    log_path: Path,
) -> dict[str, Any]:
    script = (
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
        f"cd {shlex.quote(case_dir_linux)}; "
        f"{command}"
    )
    result = _run_wsl(distro, script, timeout_s)
    log_text = result.stdout
    if result.stderr:
        log_text += result.stderr
    log_path.write_text(log_text, encoding="utf-8")
    return {
        "command": command,
        "returncode": result.returncode,
        "log": str(log_path),
    }


def parse_icofoam_log(log_text: str) -> dict[str, Any]:
    times = [_float(match.group(1)) for match in TIME_RE.finditer(log_text)]
    courant_history = [
        {"mean": _float(match.group(1)), "max": _float(match.group(2))}
        for match in COURANT_RE.finditer(log_text)
    ]
    residual_history = []
    last_residuals: dict[str, dict[str, Any]] = {}
    for match in RESIDUAL_RE.finditer(log_text):
        item = {
            "field": match.group("field"),
            "initial": _float(match.group("initial")),
            "final": _float(match.group("final")),
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
            "sum_local": _float(match.group("local")),
            "global": _float(match.group("global")),
            "cumulative": _float(match.group("cumulative")),
        }
        for match in CONTINUITY_RE.finditer(log_text)
    ]
    floating_exception = any(
        "Floating point exception" in item and "trapping enabled" not in item
        for item in log_text.splitlines()
    )
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or floating_exception
    return {
        "started": "Starting time loop" in log_text,
        "fatal_error_detected": fatal,
        "times": times,
        "final_time": times[-1] if times else None,
        "time_step_count": len(times),
        "courant_history": courant_history,
        "max_courant_number": max(
            (entry["max"] for entry in courant_history), default=None
        ),
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


def _runtime_log_path(runtime: dict[str, Any], command: str, output_dir: Path) -> Path:
    match = next((item for item in runtime.get("commands", []) if item.get("command") == command), None)
    if match and match.get("log"):
        return Path(match["log"])
    return output_dir / "logs" / f"log.{command.split()[0]}"


def build_runtime_metrics(
    config: dict[str, Any],
    output_dir: Path,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    logs = {Path(item["log"]).name: item["log"] for item in runtime["commands"]}
    solver_log = _runtime_log_path(runtime, "icoFoam", output_dir)
    check_mesh_log = _runtime_log_path(runtime, "checkMesh", output_dir)
    solver_metrics = parse_icofoam_log(
        solver_log.read_text(encoding="utf-8") if solver_log.exists() else ""
    )
    check_mesh_metrics = parse_check_mesh_log(
        check_mesh_log.read_text(encoding="utf-8") if check_mesh_log.exists() else ""
    )
    postprocess_metrics = write_centerline_profiles(config, output_dir) if solver_metrics.get("final_time") is not None else {}
    time_dirs = []
    case_dir = output_dir / "case"
    if case_dir.exists():
        for path in case_dir.iterdir():
            if path.is_dir():
                try:
                    value = float(path.name)
                except ValueError:
                    continue
                time_dirs.append({"name": path.name, "time": value})
        time_dirs.sort(key=lambda item: item["time"])
    return {
        "schema_version": "openfoam_c01_metrics_v1",
        "parser": {
            "name": "openfoam_c01_log_parser",
            "version": 1,
            "limitations": [
                "Parses icoFoam/checkMesh health metrics and extracts final-time centerline CSV profiles."
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


def validate_runtime_metrics(
    metrics: dict[str, Any], config: dict[str, Any], output_dir: Path
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    commands = metrics["runtime"].get("commands", [])
    for command in config["solver"]["command_sequence"]:
        match = next((item for item in commands if item["command"] == command), None)
        check(
            f"command.{command}.returncode",
            bool(match and match["returncode"] == 0),
            json.dumps(match or {}, ensure_ascii=False),
        )

    mesh_metrics = metrics.get("mesh", {})
    check(
        "mesh.checkMesh_ok",
        mesh_metrics.get("mesh_ok") is True,
        json.dumps(mesh_metrics, ensure_ascii=False),
    )
    solver = metrics["solver"]
    end_time = float(config["numerics"]["control"]["end_time_s"])
    final_time = solver.get("final_time")
    check("solver.started", solver.get("started") is True, "Starting time loop found")
    check(
        "solver.no_fatal_error",
        solver.get("fatal_error_detected") is False,
        "FOAM FATAL and floating point exception must be absent",
    )
    check(
        "solver.final_time",
        _is_finite(final_time) and float(final_time) >= end_time - 1e-12,
        f"final_time={final_time}, expected_end_time={end_time}",
    )
    max_courant = solver.get("max_courant_number")
    max_allowed = float(config["validation"]["max_courant_number"])
    check(
        "solver.max_courant_number",
        _is_finite(max_courant) and float(max_courant) <= max_allowed,
        f"max_courant_number={max_courant}, threshold={max_allowed}",
    )
    residual_values = [
        value
        for item in solver.get("residual_history", [])
        for value in (item.get("initial"), item.get("final"))
    ]
    check(
        "solver.residuals_finite",
        bool(residual_values) and all(_is_finite(value) for value in residual_values),
        f"residual_count={len(residual_values)}",
    )
    last_continuity = solver.get("last_continuity") or {}
    check(
        "solver.continuity_finite",
        bool(last_continuity)
        and all(_is_finite(value) for value in last_continuity.values()),
        json.dumps(last_continuity, ensure_ascii=False),
    )
    for rel_path in config["validation"]["required_generated_files"]:
        path = output_dir / rel_path
        check(
            f"artifact.generated.{rel_path}",
            path.exists() and path.stat().st_size > 0,
            str(path),
        )
    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        if rel_path == "logs/log.blockMesh":
            path = _runtime_log_path(metrics["runtime"], "blockMesh", output_dir)
        elif rel_path == "logs/log.checkMesh":
            path = _runtime_log_path(metrics["runtime"], "checkMesh", output_dir)
        elif rel_path == "logs/log.icoFoam":
            path = _runtime_log_path(metrics["runtime"], "icoFoam", output_dir)
        check(
            f"artifact.expected.{rel_path}",
            path.exists() and path.stat().st_size > 0,
            str(path),
        )
    profiles = metrics.get("postprocess", {}).get("profiles", {})
    expected_profile_rows = {
        "vertical_centerline_Ux": int(config["mesh"]["cells"][1]) + 1,
        "horizontal_centerline_Uy": int(config["mesh"]["cells"][0]) + 1,
    }
    for profile_name, expected_rows in expected_profile_rows.items():
        profile = profiles.get(profile_name, {})
        path = Path(profile.get("path", ""))
        stats = profile.get("stats", {})
        check(
            f"postprocess.{profile_name}.csv",
            path.exists() and path.stat().st_size > 0,
            str(path),
        )
        check(
            f"postprocess.{profile_name}.row_count",
            int(profile.get("sample_count", 0)) >= expected_rows,
            f"sample_count={profile.get('sample_count')}, expected>={expected_rows}",
        )
        check(
            f"postprocess.{profile_name}.finite_monotonic",
            stats.get("finite") is True and stats.get("coordinate_monotonic") is True,
            json.dumps(stats, ensure_ascii=False),
        )

    required_artifacts = {
        "logs/log.blockMesh": _runtime_log_path(metrics["runtime"], "blockMesh", output_dir),
        "logs/log.checkMesh": _runtime_log_path(metrics["runtime"], "checkMesh", output_dir),
        "logs/log.icoFoam": _runtime_log_path(metrics["runtime"], "icoFoam", output_dir),
        "metrics.json": output_dir / "metrics.json",
    }
    for rel_path, path in required_artifacts.items():
        check(
            f"artifact.{rel_path}",
            path.exists() and path.stat().st_size > 0,
            str(path),
        )
    final_time_dir = output_dir / "case" / f"{end_time:g}"
    check(
        "artifact.final_time_directory",
        final_time_dir.exists(),
        str(final_time_dir),
    )
    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local WSL OpenFOAM runtime smoke; no perturbation or benchmark-reference comparison",
        "checks": checks,
    }


def write_runtime_report(
    config: dict[str, Any],
    metrics: dict[str, Any],
    validation: dict[str, Any],
    output_dir: Path,
) -> None:
    solver = metrics["solver"]
    status = "passed" if validation["passed"] else "failed"
    logs = metrics.get("artifacts", {}).get("logs", {})
    lines = [
        f"# OpenFOAM C01 {config['case_id']} runtime report",
        "",
        f"- gate: `{validation['gate']}`",
        f"- status: `{status}`",
        f"- backend: `{config['backend']['type']}`",
        f"- runtime profile: `{config['openfoam']['runtime_profile']}`",
        f"- OpenFOAM version: `{metrics['runtime']['profile_env'].get('WM_PROJECT_VERSION', '')}`",
        f"- final time: `{solver.get('final_time')}`",
        f"- max Courant number: `{solver.get('max_courant_number')}`",
        f"- time steps parsed: `{solver.get('time_step_count')}`",
        "",
        "## Artifacts",
        "",
        "- `manifest.json`",
        "- `metrics.json`",
        "- `validation.json`",
        f"- blockMesh log: `{logs.get('log.01_blockMesh', logs.get('log.blockMesh', ''))}`",
        f"- checkMesh log: `{logs.get('log.02_checkMesh', logs.get('log.checkMesh', ''))}`",
        f"- icoFoam log: `{logs.get('log.03_icoFoam', logs.get('log.icoFoam', ''))}`",
        "- `postprocess/centerline_vertical_Ux.csv`",
        "- `postprocess/centerline_horizontal_Uy.csv`",
        "",
        "## Scope",
        "",
        "This report validates one local runtime case and final-time centerline CSV extraction. Matrix-level trend checks are recorded in the benchmark validation report.",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
