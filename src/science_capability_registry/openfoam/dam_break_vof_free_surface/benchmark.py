"""Benchmark matrix orchestration for OpenFOAM C06."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .runner import run

DEFAULT_CONFIGS = [
    Path("configs/openfoam/dam_break_vof_free_surface/baseline_wsl_v2112.yaml"),
    Path("configs/openfoam/dam_break_vof_free_surface/mesh_refined_wsl_v2112.yaml"),
    Path("configs/openfoam/dam_break_vof_free_surface/gravity_half_wsl_v2112.yaml"),
    Path("configs/openfoam/dam_break_vof_free_surface/water_height_125pct_wsl_v2112.yaml"),
]
REPORT_PATH = Path("reports/openfoam_C06_dam_break_vof_free_surface_benchmark_validation.md")
BENCHMARK_DIR = Path("_results/openfoam/dam_break_vof_free_surface/benchmark_matrix")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_case(path: Path) -> dict[str, Any]:
    config = _load_yaml(path)
    output_dir = Path(config["outputs"]["output_dir"])
    return {"config": config, "metrics": json.loads((output_dir / "metrics.json").read_text(encoding="utf-8")), "validation": json.loads((output_dir / "validation.json").read_text(encoding="utf-8")), "output_dir": output_dir}


def validate_benchmark_matrix(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    required = ["baseline_wsl_v2112", "mesh_refined_wsl_v2112", "gravity_half_wsl_v2112", "water_height_125pct_wsl_v2112"]
    for case_id in required:
        check(f"case.present.{case_id}", case_id in cases, case_id)
    if any(case_id not in cases for case_id in required):
        return {"passed": False, "gate": "integration", "checks": checks}
    for case_id, case in cases.items():
        check(f"case.{case_id}.runtime_validation", case["validation"].get("passed") is True, str(case["output_dir"]))
        profiles = case["metrics"].get("postprocess", {}).get("profiles", {})
        check(f"case.{case_id}.postprocess_profiles_present", bool(profiles), str(case["output_dir"]))
        for name, profile in profiles.items():
            artifact_path = Path(profile.get("path", ""))
            check(
                f"case.{case_id}.artifact.{name}",
                artifact_path.exists() and artifact_path.stat().st_size > 0,
                str(artifact_path),
            )
    baseline = cases["baseline_wsl_v2112"]
    mesh = cases["mesh_refined_wsl_v2112"]
    gravity = cases["gravity_half_wsl_v2112"]
    height = cases["water_height_125pct_wsl_v2112"]
    base_front = float(baseline["metrics"]["postprocess"]["front"]["front_x_m"])
    mesh_front = float(mesh["metrics"]["postprocess"]["front"]["front_x_m"])
    gravity_front = float(gravity["metrics"]["postprocess"]["front"]["front_x_m"])
    height_front = float(height["metrics"]["postprocess"]["front"]["front_x_m"])
    base_volume = float(baseline["metrics"]["postprocess"]["volume"]["water_volume_m3"])
    height_volume = float(height["metrics"]["postprocess"]["volume"]["water_volume_m3"])
    check("trend.mesh_refined.front_same_order", abs(mesh_front - base_front) <= 0.08, f"mesh_front={mesh_front:.6g}, baseline={base_front:.6g}")
    check("trend.gravity_half.front_slower", gravity_front < base_front, f"gravity_front={gravity_front:.6g}, baseline={base_front:.6g}")
    check("trend.water_height_125pct.volume_increases", height_volume > base_volume * 1.15, f"height_volume={height_volume:.6g}, baseline={base_volume:.6g}")
    check("trend.water_height_125pct.front_not_slower", height_front >= base_front * 0.95, f"height_front={height_front:.6g}, baseline={base_front:.6g}")
    return {"passed": all(item["passed"] for item in checks), "gate": "integration", "checks": checks}


def _write_case_summary(cases: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "gravity_m_s2", "water_height_m", "mesh_scale", "front_x_m", "water_volume_m3", "volume_relative_error", "validation_passed"])
        writer.writeheader()
        for case_id, case in cases.items():
            config = case["config"]
            post = case["metrics"]["postprocess"]
            writer.writerow({"case_id": case_id, "gravity_m_s2": config["physics"]["gravity_m_s2"], "water_height_m": config["initial_conditions"]["water_column_height_m"], "mesh_scale": config["mesh"]["cell_count_scale"], "front_x_m": post["front"]["front_x_m"], "water_volume_m3": post["volume"]["water_volume_m3"], "volume_relative_error": post["volume"]["relative_error"], "validation_passed": case["validation"]["passed"]})


def _read_front(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_plots(cases: dict[str, dict[str, Any]], plot_dir: Path) -> list[str]:
    plot_dir.mkdir(parents=True, exist_ok=True)
    front_plot = plot_dir / "front_position_history.png"
    volume_plot = plot_dir / "water_volume_error_history.png"
    plt.figure(figsize=(7, 4))
    for case_id, case in cases.items():
        rows = _read_front(Path(case["metrics"]["postprocess"]["profiles"]["front_position_history"]["path"]))
        plt.plot([float(row["time_s"]) for row in rows], [float(row["front_x_m"]) for row in rows], label=case_id)
    plt.xlabel("time (s)")
    plt.ylabel("front x (m)")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(front_plot, dpi=160)
    plt.close()
    plt.figure(figsize=(7, 4))
    for case_id, case in cases.items():
        path = Path(case["metrics"]["postprocess"]["profiles"]["water_volume_history"]["path"])
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        plt.plot([float(row["time_s"]) for row in rows], [float(row["relative_error"]) for row in rows], label=case_id)
    plt.xlabel("time (s)")
    plt.ylabel("water volume relative error")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(volume_plot, dpi=160)
    plt.close()
    return [str(front_plot), str(volume_plot)]


def _write_report(cases: dict[str, dict[str, Any]], validation: dict[str, Any], summary_csv: Path, plots: list[str], report_path: Path = REPORT_PATH) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = ["# OpenFOAM C06 benchmark validation report", "", "## Scope", "", "- capability: C06_dam_break_vof_free_surface", "- gate: integration", f"- matrix status: {status}", "- runtime profile: openfoam_com_v2112", "- WSL distro: Ubuntu-24.04", f"- benchmark summary: {summary_csv}", "", "## Case Matrix", ""]
    for case_id, case in cases.items():
        config = case["config"]
        post = case["metrics"]["postprocess"]
        lines.append(f"- {case_id}: g={config['physics']['gravity_m_s2']}, h0={config['initial_conditions']['water_column_height_m']}, mesh_scale={config['mesh']['cell_count_scale']}, front_x={post['front']['front_x_m']}, volume_error={post['volume']['relative_error']}, validation={case['validation']['passed']}")
    lines.extend(["", "## Trend Checks", ""])
    for item in validation["checks"]:
        if item["name"].startswith("trend."):
            mark = "passed" if item["passed"] else "failed"
            lines.append(f"- {item['name']}: {mark}; {item['details']}")
    lines.extend(["", "## Numeric Artifacts", "", f"- case summary CSV: {summary_csv}"])
    for plot in plots:
        lines.append(f"- plot: {plot}")
    lines.extend(["", "## Status Conclusion", ""])
    if validation["passed"]:
        lines.append("The four-case local WSL v2112 matrix passed solver health, alpha boundedness, water-volume, front-propagation, artifact, and perturbation trend checks for the registry-local C06 scope.")
    else:
        lines.append("The matrix did not fully pass. Do not promote benchmark_status.")
        for item in validation["checks"]:
            if not item["passed"]:
                lines.append(f"- failed {item['name']}: {item['details']}")
    lines.extend(["", "## Residual Risk", "", "- Evidence is local OpenFOAM.com v2112 only.", "- The horizon is the configured short integration horizon, not a full experimental dam-break reference comparison.", "- The OpenFOAM sampling functionObject is disabled because this local OpenFOAM.com v2112 WSL profile triggers a sha1 IO error, including ext4 probe paths; Python alpha-field postprocess is used instead.", "- This is laminar interFoam VOF only; RAS damBreak and four-phase tutorials are out of scope."])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_benchmark_matrix(config_paths: list[Path] | None = None) -> dict[str, Any]:
    paths = config_paths or DEFAULT_CONFIGS
    for path in paths:
        result = run(config_path=path)
        if not result.get("validation", {}).get("passed", False):
            break
    cases = {}
    for path in paths:
        loaded = _load_case(path)
        cases[loaded["config"]["case_id"]] = loaded
    validation = validate_benchmark_matrix(cases)
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    validation_path = BENCHMARK_DIR / "benchmark_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    summary_csv = BENCHMARK_DIR / "case_summary.csv"
    _write_case_summary(cases, summary_csv)
    plots = _write_plots(cases, BENCHMARK_DIR / "plots")
    _write_report(cases, validation, summary_csv, plots)
    return {"validation": validation, "cases": list(cases), "summary_csv": str(summary_csv), "plots": plots}


def main() -> int:
    result = run_benchmark_matrix()
    print(json.dumps(result, indent=2))
    return 0 if result["validation"].get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
