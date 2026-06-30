"""Benchmark matrix orchestration for OpenFOAM C03."""

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
    Path("configs/openfoam/backward_facing_step_rans_internal_flow/baseline_wsl_v2112.yaml"),
    Path("configs/openfoam/backward_facing_step_rans_internal_flow/mesh_refined_wsl_v2112.yaml"),
    Path("configs/openfoam/backward_facing_step_rans_internal_flow/inlet_velocity_high_wsl_v2112.yaml"),
    Path("configs/openfoam/backward_facing_step_rans_internal_flow/inlet_velocity_low_wsl_v2112.yaml"),
]
REPORT_PATH = Path("reports/openfoam_C03_backward_facing_step_rans_internal_flow_benchmark_validation.md")
BENCHMARK_DIR = Path("_results/openfoam/backward_facing_step_rans_internal_flow/benchmark_matrix")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_case(path: Path) -> dict[str, Any]:
    config = _load_yaml(path)
    output_dir = Path(config["outputs"]["output_dir"])
    return {
        "config": config,
        "metrics": json.loads((output_dir / "metrics.json").read_text(encoding="utf-8")),
        "validation": json.loads((output_dir / "validation.json").read_text(encoding="utf-8")),
        "output_dir": output_dir,
    }


def validate_benchmark_matrix(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    required = ["baseline_wsl_v2112", "mesh_refined_wsl_v2112", "inlet_velocity_high_wsl_v2112", "inlet_velocity_low_wsl_v2112"]
    for case_id in required:
        check(f"case.present.{case_id}", case_id in cases, case_id)
    if any(case_id not in cases for case_id in required):
        return {"passed": False, "gate": "integration", "checks": checks}
    for case_id, case in cases.items():
        check(f"case.{case_id}.runtime_validation", case["validation"].get("passed") is True, str(case["output_dir"]))
        for name, profile in case["metrics"].get("postprocess", {}).get("profiles", {}).items():
            path = Path(profile.get("path", ""))
            check(f"case.{case_id}.artifact.{name}", path.exists() and path.stat().st_size > 0, str(path))

    baseline = cases["baseline_wsl_v2112"]
    mesh = cases["mesh_refined_wsl_v2112"]
    high = cases["inlet_velocity_high_wsl_v2112"]
    low = cases["inlet_velocity_low_wsl_v2112"]
    base_drop = float(baseline["metrics"]["postprocess"]["pressure"]["pressure_drop_kinematic_m2_s2"])
    mesh_drop = float(mesh["metrics"]["postprocess"]["pressure"]["pressure_drop_kinematic_m2_s2"])
    high_drop = float(high["metrics"]["postprocess"]["pressure"]["pressure_drop_kinematic_m2_s2"])
    low_drop = float(low["metrics"]["postprocess"]["pressure"]["pressure_drop_kinematic_m2_s2"])
    check("trend.mesh_refined.pressure_drop_same_order", 0.4 * base_drop <= mesh_drop <= 2.5 * base_drop, f"mesh_drop={mesh_drop:.6g}, baseline={base_drop:.6g}")
    check("trend.inlet_velocity_high.pressure_drop_increases", high_drop > base_drop * 1.3, f"high_drop={high_drop:.6g}, baseline={base_drop:.6g}")
    check("trend.inlet_velocity_low.pressure_drop_decreases", low_drop < base_drop * 0.9, f"low_drop={low_drop:.6g}, baseline={base_drop:.6g}")
    base_speed = float(baseline["metrics"]["postprocess"]["field_stats"]["max_speed_m_s"])
    high_speed = float(high["metrics"]["postprocess"]["field_stats"]["max_speed_m_s"])
    low_speed = float(low["metrics"]["postprocess"]["field_stats"]["max_speed_m_s"])
    check("trend.inlet_velocity.speed_response", high_speed > base_speed > low_speed, f"low={low_speed:.6g}, baseline={base_speed:.6g}, high={high_speed:.6g}")
    return {"passed": all(item["passed"] for item in checks), "gate": "integration", "checks": checks}


def _write_case_summary(cases: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "inlet_velocity_m_s", "reynolds_number_H", "mesh_scale", "pressure_drop", "max_speed", "reattachment_x_over_H", "validation_passed"])
        writer.writeheader()
        for case_id, case in cases.items():
            config = case["config"]
            post = case["metrics"]["postprocess"]
            writer.writerow({
                "case_id": case_id,
                "inlet_velocity_m_s": config["material"]["inlet_velocity_m_s"],
                "reynolds_number_H": config["material"]["reynolds_number_H"],
                "mesh_scale": config["mesh"]["cell_count_scale"],
                "pressure_drop": post["pressure"]["pressure_drop_kinematic_m2_s2"],
                "max_speed": post["field_stats"]["max_speed_m_s"],
                "reattachment_x_over_H": post["wall"].get("reattachment_length_over_H"),
                "validation_passed": case["validation"]["passed"],
            })


def _read_shear(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_plots(cases: dict[str, dict[str, Any]], plot_dir: Path) -> list[str]:
    plot_dir.mkdir(parents=True, exist_ok=True)
    pressure_plot = plot_dir / "pressure_drop_vs_inlet_velocity.png"
    shear_plot = plot_dir / "lower_wall_shear_comparison.png"
    velocities = [float(case["config"]["material"]["inlet_velocity_m_s"]) for case in cases.values()]
    drops = [float(case["metrics"]["postprocess"]["pressure"]["pressure_drop_kinematic_m2_s2"]) for case in cases.values()]
    labels = list(cases)
    plt.figure(figsize=(6, 4))
    plt.scatter(velocities, drops)
    for velocity, drop, label in zip(velocities, drops, labels):
        plt.annotate(label, (velocity, drop), fontsize=7)
    plt.xlabel("inlet velocity (m/s)")
    plt.ylabel("kinematic pressure drop (m2/s2)")
    plt.tight_layout()
    plt.savefig(pressure_plot, dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    for case_id, case in cases.items():
        shear_path = Path(case["metrics"]["postprocess"]["profiles"]["lower_wall_shear"]["path"])
        rows = _read_shear(shear_path)
        plt.plot([float(row["x_over_H"]) for row in rows], [float(row["tau_w_kinematic_m2_s2"]) for row in rows], label=case_id)
    plt.axhline(0.0, color="black", linewidth=0.7)
    plt.xlabel("x / H")
    plt.ylabel("near-wall shear proxy (m2/s2)")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(shear_plot, dpi=160)
    plt.close()
    return [str(pressure_plot), str(shear_plot)]


def _write_report(cases: dict[str, dict[str, Any]], validation: dict[str, Any], summary_csv: Path, plots: list[str], report_path: Path = REPORT_PATH) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        "# OpenFOAM C03 benchmark validation report",
        "",
        "## Scope",
        "",
        "- capability: C03_backward_facing_step_rans_internal_flow",
        "- gate: integration",
        f"- matrix status: {status}",
        "- runtime profile: openfoam_com_v2112",
        "- WSL distro: Ubuntu-24.04",
        f"- benchmark summary: {summary_csv}",
        "",
        "## Case Matrix",
        "",
    ]
    for case_id, case in cases.items():
        config = case["config"]
        post = case["metrics"]["postprocess"]
        lines.append(f"- {case_id}: Uin={config['material']['inlet_velocity_m_s']}, Re_H={config['material']['reynolds_number_H']}, mesh_scale={config['mesh']['cell_count_scale']}, pressure_drop={post['pressure']['pressure_drop_kinematic_m2_s2']}, validation={case['validation']['passed']}")
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
        lines.append("The four-case local WSL v2112 matrix passed solver health, Python field postprocess, artifact completeness, and pressure/velocity trend checks. This supports benchmark_validated status for the registry-local OpenFOAM.com v2112 C03 scope.")
    else:
        lines.append("The matrix did not fully pass. Do not promote benchmark_status.")
        for item in validation["checks"]:
            if not item["passed"]:
                lines.append(f"- failed {item['name']}: {item['details']}")
    lines.extend(["", "## Residual Risk", "", "- Evidence is local OpenFOAM.com v2112 only; Foundation/OpenFOAM-dev compatibility is not covered.", "- The wall shear and yPlus outputs are Python near-wall proxy metrics because this local OpenFOAM.com v2112 WSL profile triggers a sha1 IO error, including ext4 probe paths.", "- This is not an external Pitz & Daily experimental validation or mesh-independent RANS study."])
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
