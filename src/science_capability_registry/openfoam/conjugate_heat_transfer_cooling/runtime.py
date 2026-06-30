"""OpenFOAM runtime execution and log parsing for C07."""

from __future__ import annotations

import json
import math
import re
import shlex
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import (
    map_windows_path_to_wsl,
    profile_env,
    resolve_runtime_identity,
    run_openfoam_command,
    run_wsl,
)

from .postprocess import write_interface_balance_summary, write_region_temperature_summary

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TIME_RE = re.compile(rf"^Time =\s*({FLOAT_RE})", re.MULTILINE)
REGION_RE = re.compile(r"Solving for\s+(?:fluid|solid)\s+region\s+([A-Za-z0-9_]+)")
CREATE_REGION_RE = re.compile(r"Create\s+(?:fluid|solid)\s+mesh\s+for\s+region\s+([A-Za-z0-9_]+)")
RESIDUAL_RE = re.compile(
    rf"(?:\w+:\s+)?Solving for\s+(?P<field>[\w.()_-]+),\s+"
    rf"Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+"
    r"No Iterations\s+(?P<iterations>\d+)"
)
CONTINUITY_RE = re.compile(
    rf"time step continuity errors\s*:\s*sum local =\s*(?P<local>{FLOAT_RE}),\s+"
    rf"global =\s*(?P<global>{FLOAT_RE}),\s+cumulative =\s*(?P<cumulative>{FLOAT_RE})"
)
CHECK_MESH_OK_RE = re.compile(r"Mesh OK", re.IGNORECASE)


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def _fatal_error(log_text: str) -> bool:
    return "FOAM FATAL" in log_text or "FOAM exiting" in log_text or "Segmentation fault" in log_text or _true_floating_exception(log_text)


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def parse_chtmultiregion_log(log_text: str) -> dict[str, Any]:
    """Parse chtMultiRegionSimpleFoam region, residual, and continuity signals."""

    times = [float(match.group(1)) for match in TIME_RE.finditer(log_text)]
    regions_seen: set[str] = set()
    current_region = "global"
    residual_history = []
    last_residuals: dict[str, dict[str, Any]] = {}
    continuity_history = []

    for line in log_text.splitlines():
        create_region_match = CREATE_REGION_RE.search(line)
        if create_region_match:
            regions_seen.add(create_region_match.group(1))
            continue
        region_match = REGION_RE.search(line)
        if region_match:
            current_region = region_match.group(1)
            regions_seen.add(current_region)
            continue
        residual_match = RESIDUAL_RE.search(line)
        if residual_match:
            item = {
                "region": current_region,
                "field": residual_match.group("field"),
                "initial": float(residual_match.group("initial")),
                "final": float(residual_match.group("final")),
                "iterations": int(residual_match.group("iterations")),
            }
            residual_history.append(item)
            last_residuals.setdefault(current_region, {})[item["field"]] = {
                "initial": item["initial"],
                "final": item["final"],
                "iterations": item["iterations"],
            }
            continue
        continuity_match = CONTINUITY_RE.search(line)
        if continuity_match:
            continuity_history.append(
                {
                    "region": current_region,
                    "sum_local": float(continuity_match.group("local")),
                    "global": float(continuity_match.group("global")),
                    "cumulative": float(continuity_match.group("cumulative")),
                }
            )

    return {
        "started": bool(times or regions_seen or residual_history),
        "fatal_error_detected": _fatal_error(log_text),
        "times": times,
        "final_time": times[-1] if times else None,
        "iteration_count": len(times),
        "regions_seen": sorted(regions_seen),
        "region_count": len(regions_seen),
        "residual_history": residual_history,
        "last_residuals": last_residuals,
        "continuity_history": continuity_history,
        "last_continuity": continuity_history[-1] if continuity_history else None,
    }


def parse_check_mesh_log(log_text: str) -> dict[str, Any]:
    """Parse the minimum multi-region checkMesh signal."""

    regions_seen = sorted(set(re.findall(r"Create mesh for time = .*? region ([A-Za-z0-9_]+)", log_text)))
    return {
        "ran": bool(log_text.strip()),
        "mesh_ok": bool(CHECK_MESH_OK_RE.search(log_text)) and not _fatal_error(log_text),
        "fatal_error_detected": _fatal_error(log_text),
        "regions_seen": regions_seen,
        "region_count": len(regions_seen),
        "cell_count": [int(value) for value in re.findall(r"cells:\s+(\d+)", log_text)],
        "max_non_orthogonality": _last_float(r"Max\s+non-orthogonality\s*=\s*(" + FLOAT_RE + r")", log_text),
        "max_skewness": _last_float(r"Max\s+skewness\s*=\s*(" + FLOAT_RE + r")", log_text),
        "max_aspect_ratio": _last_float(r"Max\s+aspect\s+ratio\s*=\s*(" + FLOAT_RE + r")", log_text),
    }


def _last_float(pattern: str, text: str) -> float | None:
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return float(matches[-1]) if matches else None


def _command_slug(command: str) -> str:
    for token in [
        "blockMesh",
        "surfaceFeatureExtract",
        "snappyHexMesh",
        "decomposePar",
        "restore0Dir",
        "splitMeshRegions",
        "topoSet",
        "checkMesh",
        "chtMultiRegionSimpleFoam",
        "reconstructParMesh",
        "reconstructPar",
    ]:
        if token in command:
            return token
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", command.split()[0])


def _run_functions_path(bashrc_path: str) -> str:
    if bashrc_path.endswith("/etc/bashrc"):
        return bashrc_path[: -len("/etc/bashrc")] + "/bin/tools/RunFunctions"
    return "$WM_PROJECT_DIR/bin/tools/RunFunctions"


def _shell_command(command: str, bashrc_path: str) -> str:
    if command == "restore0Dir -processor":
        return f". {shlex.quote(_run_functions_path(bashrc_path))}; restore0Dir -processor"
    return command


def _runtime_commands(config: dict[str, Any]) -> list[str]:
    return [
        *config["mesh_workflow"]["command_sequence"],
        *config["solver"]["command_sequence"],
        "reconstructParMesh -allRegions -constant",
        "reconstructPar -allRegions",
    ]


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    runtime_identity = resolve_runtime_identity(config)
    distro = runtime_identity["wsl_distro"]
    bashrc_path = runtime_identity["bashrc_path"]
    timeout_s = runtime_identity["timeout_s"]
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    case_dir_linux = map_windows_path_to_wsl(output_dir / "case", distro, timeout_s)
    env = profile_env(distro, bashrc_path, timeout_s)

    executable_checks = {}
    for executable in runtime_identity["required_executables"]:
        script = f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; command -v {shlex.quote(executable)}"
        result = run_wsl(distro, script, timeout_s)
        executable_checks[executable] = {
            "returncode": result.returncode,
            "path": result.stdout.strip().splitlines()[0] if result.stdout.strip() else "",
        }
        if result.returncode != 0:
            raise RuntimeError(f"Required OpenFOAM executable not found: {executable}")

    command_results = []
    for index, command in enumerate(_runtime_commands(config), start=1):
        log_path = logs_dir / f"log.{index:02d}_{_command_slug(command)}"
        result = run_openfoam_command(
            distro=distro,
            bashrc_path=bashrc_path,
            case_dir_linux=case_dir_linux,
            command=_shell_command(command, bashrc_path),
            timeout_s=timeout_s,
            log_path=log_path,
        )
        result["command"] = command
        command_results.append(result)
        if result["returncode"] != 0:
            break

    return {
        "backend": "wsl",
        "runtime_profile": runtime_identity["runtime_profile"],
        "profile_source": runtime_identity["profile_source"],
        "wsl_distro": distro,
        "bashrc_path": bashrc_path,
        "profile_env": env,
        "case_dir_linux": case_dir_linux,
        "required_executables": executable_checks,
        "commands": command_results,
    }


def _command_log(runtime: dict[str, Any], token: str) -> Path | None:
    for item in runtime.get("commands", []):
        if token in item.get("command", ""):
            return Path(item["log"])
    return None


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    solver_log = _command_log(runtime, "chtMultiRegionSimpleFoam")
    check_mesh_log = _command_log(runtime, "checkMesh")
    solver_metrics = parse_chtmultiregion_log(solver_log.read_text(encoding="utf-8") if solver_log and solver_log.exists() else "")
    check_mesh_metrics = parse_check_mesh_log(
        check_mesh_log.read_text(encoding="utf-8") if check_mesh_log and check_mesh_log.exists() else ""
    )
    temperature_metrics = write_region_temperature_summary(config, output_dir, solver_metrics.get("final_time"))
    interface_metrics = write_interface_balance_summary(config, output_dir, temperature_metrics)
    logs = {Path(item["log"]).name: item["log"] for item in runtime["commands"]}
    return {
        "schema_version": "openfoam_c07_metrics_v1",
        "parser": {
            "name": "openfoam_c07_log_and_field_parser",
            "version": 1,
            "limitations": [
                "Interface balance is a region-mean temperature proxy in the smoke gate, not native patch heat-flux conservation.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "mesh": check_mesh_metrics,
        "solver": solver_metrics,
        "postprocess": {
            "temperatures": temperature_metrics,
            "interfaces": interface_metrics,
        },
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def _expected_regions(config: dict[str, Any]) -> set[str]:
    return set(_runtime_region for _runtime_region in [*config["regions"]["fluid"], *config["regions"]["solid"]])


def _max_final_residual(solver: dict[str, Any]) -> float:
    values = []
    for fields in solver.get("last_residuals", {}).values():
        for residual in fields.values():
            value = residual.get("final")
            if _is_finite(value):
                values.append(float(value))
    return max(values, default=float("inf"))


def _temperatures_within_bounds(metrics: dict[str, Any], lower: float, upper: float) -> bool:
    rows = metrics.get("postprocess", {}).get("temperatures", {}).get("regions", [])
    if not rows:
        return False
    for row in rows:
        if not row.get("available") or not row.get("finite"):
            return False
        if not (_is_finite(row.get("min_T_K")) and _is_finite(row.get("max_T_K"))):
            return False
        if float(row["min_T_K"]) < lower or float(row["max_T_K"]) > upper:
            return False
    return True


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    runtime = metrics.get("runtime", {})
    for command in _runtime_commands(config):
        match = next((item for item in runtime.get("commands", []) if item["command"] == command), None)
        check(f"command.{_command_slug(command)}.returncode", bool(match and match["returncode"] == 0), json.dumps(match or {}, ensure_ascii=False))

    mesh = metrics.get("mesh", {})
    check("mesh.checkMesh_ok", mesh.get("mesh_ok") is True, json.dumps(mesh, ensure_ascii=False))

    solver = metrics.get("solver", {})
    end_time = float(config["numerics"]["control"]["end_time_iterations"])
    final_time = solver.get("final_time")
    expected_regions = _expected_regions(config)
    seen_regions = set(solver.get("regions_seen", []))
    check("solver.started", solver.get("started") is True, "time, region, or residual signal found")
    check("solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    check("solver.final_time", _is_finite(final_time) and float(final_time) >= end_time - 1e-12, f"final_time={final_time}, expected={end_time}")
    check("solver.all_regions_seen", expected_regions.issubset(seen_regions), f"seen={sorted(seen_regions)}, expected={sorted(expected_regions)}")
    max_final = _max_final_residual(solver)
    residual_threshold = float(config["validation"]["max_final_residual"])
    check("solver.final_residual_threshold", math.isfinite(max_final) and max_final <= residual_threshold, f"max_final_residual={max_final}, threshold={residual_threshold}")

    lower = float(config["validation"]["temperature_min_K"])
    upper = float(config["validation"]["temperature_max_K"])
    check("postprocess.temperature_bounds", _temperatures_within_bounds(metrics, lower, upper), f"bounds={[lower, upper]}")
    interfaces = metrics.get("postprocess", {}).get("interfaces", {})
    check("postprocess.interface_proxy_available", interfaces.get("available") is True, json.dumps(interfaces, ensure_ascii=False))

    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        check(f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "benchmark_status": "runtime_smoke_verified" if all(item["passed"] for item in checks) else "runtime_smoke_failed",
        "scope": "local WSL OpenFOAM C07 runtime smoke; interface heat-flux conservation remains targeted validation",
        "checks": checks,
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    status = "passed" if validation["passed"] else "failed"
    solver = metrics.get("solver", {})
    lines = [
        f"# OpenFOAM C07 {config['case_id']} runtime smoke report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime profile: {config['openfoam']['runtime_profile']}",
        f"- final pseudo-time: {solver.get('final_time')}",
        f"- regions seen: {', '.join(solver.get('regions_seen', []))}",
        "",
        "## Checks",
        "",
    ]
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This smoke gate validates OpenFOAM command wiring, multi-region solver coverage, residuals, reconstructed temperature fields, and artifact completeness. Interface heat-flux conservation is not claimed by this gate.",
        ]
    )
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
