"""OpenFOAM runtime execution and log parsing for C08."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.field_io import read_internal_scalars, read_internal_vectors
from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import compute_boundary_flux_conservation_proxy, summarize_field_extrema, write_conservation_summary, write_shock_metrics
from .validation import validate_runtime_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
COURANT_RE = re.compile(
    rf"(?:Courant Number.*?mean:\s*(?P<mean_colon>{FLOAT_RE}).*?max:\s*(?P<max_colon>{FLOAT_RE})|"
    rf"Mean and max Courant Numbers\s*=\s*(?P<mean_equals>{FLOAT_RE})\s+(?P<max_equals>{FLOAT_RE}))"
)
TIME_RE = re.compile(rf"^Time\s+=\s+(?P<time>{FLOAT_RE})", re.MULTILINE)


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def parse_rhocentralfoam_log(log_text: str) -> dict[str, Any]:
    courant_history = []
    for match in COURANT_RE.finditer(log_text):
        mean_value = match.group("mean_colon") or match.group("mean_equals")
        max_value = match.group("max_colon") or match.group("max_equals")
        courant_history.append({"mean": float(mean_value), "max": float(max_value)})
    times = [float(match.group("time")) for match in TIME_RE.finditer(log_text)]
    fatal = (
        "FOAM FATAL" in log_text
        or "FOAM exiting" in log_text
        or "Segmentation fault" in log_text
        or "sigFpe::sigHandler" in log_text
        or _true_floating_exception(log_text)
    )
    started = "rhoCentralFoam" in log_text or bool(courant_history) or bool(times)
    max_courant = max((item["max"] for item in courant_history), default=math.nan)
    final_time = max(times) if times else math.nan
    return {
        "started": started,
        "fatal_error_detected": fatal,
        "courant_history": courant_history,
        "max_courant": max_courant,
        "final_time_s": final_time,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _solver_log(runtime: dict[str, Any], output_dir: Path) -> Path:
    for item in runtime.get("commands", []):
        if "rhoCentralFoam" in item.get("command", ""):
            return Path(item["log"])
    return output_dir / "logs" / "log.rhoCentralFoam"


def _numeric_time(path: Path) -> float | None:
    try:
        return float(path.name)
    except ValueError:
        return None


def _latest_time_dir(case_dir: Path) -> Path:
    candidates = []
    for path in case_dir.iterdir():
        if not path.is_dir():
            continue
        time_value = _numeric_time(path)
        if time_value is not None:
            candidates.append((time_value, path))
    if not candidates:
        raise FileNotFoundError(f"No numeric OpenFOAM time directories found under {case_dir}")
    return max(candidates, key=lambda item: item[0])[1]


def _read_final_fields(case_dir: Path) -> dict[str, list[float] | list[tuple[float, float, float]]]:
    time_dir = _latest_time_dir(case_dir)
    fields: dict[str, list[float] | list[tuple[float, float, float]]] = {}
    for field_name in ["p", "T", "rho"]:
        path = time_dir / field_name
        if path.exists():
            fields[field_name] = read_internal_scalars(path)
    velocity_path = time_dir / "U"
    if velocity_path.exists():
        fields["U"] = read_internal_vectors(velocity_path)
    return fields


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    log_path = _solver_log(runtime, output_dir)
    solver_metrics = parse_rhocentralfoam_log(log_path.read_text(encoding="utf-8") if log_path.exists() else "")
    try:
        field_extrema = summarize_field_extrema(_read_final_fields(output_dir / "case"))
    except (FileNotFoundError, ValueError) as exc:
        field_extrema = {"error": str(exc)}
    try:
        shock_metrics = write_shock_metrics(config, output_dir)
    except (FileNotFoundError, ValueError, IndexError, ZeroDivisionError) as exc:
        shock_metrics = {"available": False, "reason": str(exc)}
    try:
        conservation_details = compute_boundary_flux_conservation_proxy(config, output_dir)
        conservation = write_conservation_summary(output_dir, conservation_details)
    except (FileNotFoundError, ValueError, IndexError, ZeroDivisionError) as exc:
        conservation = write_conservation_summary(output_dir, details={"reason": str(exc)})
    logs = {Path(item["log"]).name: item["log"] for item in runtime.get("commands", [])}
    return {
        "schema_version": "openfoam_c08_metrics_v1",
        "parser": {
            "name": "openfoam_c08_rhocentralfoam_forward_step_parser",
            "version": 2,
            "limitations": [
                "Shock profile extraction uses Python cell-centre line sampling from final OpenFOAM fields.",
                "Boundary-flux balance uses owner-cell field values and oriented polyMesh face areas, not native rhoPhi/phi integration.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "solver": solver_metrics,
        "postprocess": {
            "field_extrema": field_extrema,
            "shock": shock_metrics,
            "conservation": conservation,
        },
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    solver = metrics.get("solver", {})
    shock = metrics.get("postprocess", {}).get("shock", {})
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# OpenFOAM C08 {config['case_id']} runtime report",
        "",
        f"- gate: `{validation['gate']}`",
        f"- status: `{status}`",
        f"- runtime profile: `{config['openfoam']['runtime_profile']}`",
        f"- max Courant: `{solver.get('max_courant')}`",
        f"- final time: `{solver.get('final_time_s')}`",
        f"- shock position: `{shock.get('shock_position_m')}`",
        "",
        "## Scope",
        "",
        "This report covers local rhoCentralFoam execution, solver-log parsing, field sanity, shock metrics, and boundary-flux proxy checks when runtime field samples are available.",
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
