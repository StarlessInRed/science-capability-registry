"""Postprocess and validation helpers for Fluent C01."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

RESIDUAL_NAMES = ("continuity", "x_velocity", "y_velocity", "energy", "k", "epsilon")
RESIDUAL_RE = re.compile(
    r"^\s*(?P<iteration>\d+)\s+"
    r"(?P<continuity>[-+0-9.eE]+)\s+"
    r"(?P<x_velocity>[-+0-9.eE]+)\s+"
    r"(?P<y_velocity>[-+0-9.eE]+)\s+"
    r"(?P<energy>[-+0-9.eE]+)\s+"
    r"(?P<k>[-+0-9.eE]+)\s+"
    r"(?P<epsilon>[-+0-9.eE]+)\s+"
)
MASS_ROW_RE = re.compile(r"^\s*(?P<zone>[A-Za-z0-9_.-]+)\s+(?P<value>[-+0-9.eE]+)\s*$")


def parse_residual_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = RESIDUAL_RE.match(line)
        if match is None:
            continue
        row: dict[str, Any] = {"iteration": int(match.group("iteration"))}
        for name in RESIDUAL_NAMES:
            row[name] = float(match.group(name))
        rows.append(row)
    return rows


def parse_mass_flow_reports(text: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "Mass Flow Rate" not in line:
            continue
        values: dict[str, float] = {}
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if not stripped:
                if values:
                    break
                continue
            if stripped.startswith(">"):
                break
            if set(stripped) <= {"-", " "}:
                continue
            match = MASS_ROW_RE.match(candidate)
            if match is None:
                continue
            values[match.group("zone")] = float(match.group("value"))
        if values:
            reports.append(values)
    return reports


def summarize_mass_balance(mass_report: dict[str, float], config: dict[str, Any]) -> dict[str, Any]:
    mass_config = config["reports"]["mass_flow"]
    inlet_zones = mass_config["inlet_zones"]
    outlet_zones = mass_config["outlet_zones"]
    inlet_flow = sum(mass_report.get(zone, 0.0) for zone in inlet_zones)
    outlet_flow = sum(mass_report.get(zone, 0.0) for zone in outlet_zones)
    selected_net_flow = inlet_flow + outlet_flow
    denominator = max(abs(inlet_flow), abs(outlet_flow), 1.0e-30)
    return {
        "inlet_zones": inlet_zones,
        "outlet_zones": outlet_zones,
        "inlet_mass_flow_kg_s": inlet_flow,
        "outlet_mass_flow_kg_s": outlet_flow,
        "selected_net_mass_flow_kg_s": selected_net_flow,
        "mass_imbalance_fraction": abs(selected_net_flow) / denominator,
        "reported_net_mass_flow_kg_s": mass_report.get("Net"),
    }


def collect_runtime_metrics(config: dict[str, Any], output_dir: Path, return_code: int | None) -> dict[str, Any]:
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    transcript_path = output_dir / "transcript.txt"
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    transcript_text = transcript_path.read_text(encoding="utf-8", errors="replace") if transcript_path.exists() else ""
    combined_text = "\n".join([stdout_text, stderr_text, transcript_text])
    residual_rows = parse_residual_rows(combined_text)
    final_residuals = {name: residual_rows[-1][name] for name in RESIDUAL_NAMES} if residual_rows else {}
    mass_reports = parse_mass_flow_reports(combined_text)
    final_mass_report = mass_reports[-1] if mass_reports else {}
    mass_balance = summarize_mass_balance(final_mass_report, config) if final_mass_report else {}
    output_case_base = output_dir / "fluent_c01_output.cas.h5"
    output_data_base = output_dir / "fluent_c01_output.dat.h5"
    error_lines = [line.strip() for line in combined_text.splitlines() if line.strip().startswith("Error:")]
    warning_lines = [line.strip() for line in combined_text.splitlines() if line.strip().startswith("Warning:")]
    max_residual = max(final_residuals.values()) if final_residuals else math.inf
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "return_code": return_code,
        "case_read": "Done." in combined_text and "Reading" in combined_text and ".cas" in combined_text,
        "data_read": ".dat" in combined_text and "Parallel variables" in combined_text,
        "completed_iteration_count": len(residual_rows),
        "final_iteration": residual_rows[-1]["iteration"] if residual_rows else None,
        "final_residuals": final_residuals,
        "max_residual": max_residual,
        "mass_flow_report_count": len(mass_reports),
        "mass_balance": mass_balance,
        "pressure_drop": None,
        "pressure_drop_status": "not_extracted_in_c01_smoke",
        "written_case_data": output_case_base.exists() and output_data_base.exists(),
        "written_case_path": str(output_case_base),
        "written_data_path": str(output_data_base),
        "error_lines": error_lines,
        "warning_lines": warning_lines,
    }


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
    check_artifacts: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    validation = config["validation"]
    _check(checks, "runtime.return_code", metrics.get("return_code") in (0, None), str(metrics.get("return_code")))
    if validation["require_case_read"]:
        _check(checks, "runtime.case_read", bool(metrics["case_read"]), "case file was read")
    if validation["require_data_read"]:
        _check(checks, "runtime.data_read", bool(metrics["data_read"]), "data file was read")
    if validation["require_iteration"]:
        _check(checks, "solver.iteration", metrics["completed_iteration_count"] >= 1, str(metrics["completed_iteration_count"]))
    _check(
        checks,
        "solver.max_residual",
        metrics["max_residual"] <= validation["max_residual_threshold"],
        f"{metrics['max_residual']} <= {validation['max_residual_threshold']}",
    )
    if validation["require_mass_flow_report"]:
        _check(checks, "report.mass_flow", metrics["mass_flow_report_count"] >= 1, str(metrics["mass_flow_report_count"]))
        imbalance = metrics.get("mass_balance", {}).get("mass_imbalance_fraction", math.inf)
        _check(
            checks,
            "report.mass_imbalance_fraction",
            imbalance <= validation["max_mass_imbalance_fraction"],
            f"{imbalance} <= {validation['max_mass_imbalance_fraction']}",
        )
    if validation["require_written_case_data"]:
        _check(checks, "artifact.case_data_written", bool(metrics["written_case_data"]), metrics["written_case_path"])
    _check(checks, "runtime.no_error_lines", not metrics["error_lines"], "; ".join(metrics["error_lines"]))
    if check_artifacts:
        for rel_path in validation["required_artifacts"]:
            path = output_dir / rel_path
            if rel_path == "stderr.txt":
                passed = path.exists()
            else:
                passed = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.exists.{rel_path}", passed, str(path))
    return {
        "passed": all(item["passed"] for item in checks),
        "gate": validation["gate"],
        "scope": "Fluent C01 local batch runtime smoke",
        "checks": checks,
        "details": {
            "pressure_drop_status": metrics["pressure_drop_status"],
            "allowed_warning_markers": validation["allowed_warning_markers"],
        },
    }
