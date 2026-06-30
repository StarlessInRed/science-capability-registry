"""Benchmark matrix orchestration for OpenFOAM C01."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from .postprocess import read_profile_csv
from .runner import run

DEFAULT_CONFIGS = [
    Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112.yaml"),
    Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/mesh_40x40_cfl_matched_wsl_v2112.yaml"),
    Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/re100_wsl_v2112.yaml"),
    Path("configs/openfoam/lid_driven_cavity_incompressible_laminar/dt_half_wsl_v2112.yaml"),
]
REPORT_PATH = Path("reports/openfoam_C01_lid_driven_cavity_incompressible_laminar_benchmark_validation.md")
BENCHMARK_DIR = Path("_results/openfoam/lid_driven_cavity_incompressible_laminar/benchmark_matrix")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_metrics_for_config(config_path: Path) -> dict[str, Any]:
    config = _load_yaml(config_path)
    output_dir = Path(config["outputs"]["output_dir"])
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    validation = json.loads((output_dir / "validation.json").read_text(encoding="utf-8"))
    return {"config": config, "metrics": metrics, "validation": validation, "output_dir": output_dir}


def _coordinate_key(component: str) -> str:
    return "y_over_L" if component == "Ux_m_s" else "x_over_L"


def _interpolate(rows: list[dict[str, Any]], component: str, target_s: float) -> float:
    coord_key = _coordinate_key(component)
    sorted_rows = sorted(rows, key=lambda row: float(row[coord_key]))
    if target_s <= float(sorted_rows[0][coord_key]):
        return float(sorted_rows[0][component])
    if target_s >= float(sorted_rows[-1][coord_key]):
        return float(sorted_rows[-1][component])
    for index in range(len(sorted_rows) - 1):
        left = sorted_rows[index]
        right = sorted_rows[index + 1]
        left_coord = float(left[coord_key])
        right_coord = float(right[coord_key])
        if left_coord <= target_s <= right_coord:
            weight = (target_s - left_coord) / (right_coord - left_coord)
            return float(left[component]) * (1.0 - weight) + float(right[component]) * weight
    return float(sorted_rows[-1][component])


def _mean_abs_profile_delta(
    base_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    component: str,
) -> float:
    coord_key = _coordinate_key(component)
    deltas = [
        abs(float(row[component]) - _interpolate(candidate_rows, component, float(row[coord_key])))
        for row in base_rows
    ]
    return sum(deltas) / len(deltas) if deltas else float("inf")


def _profile_rows(case: dict[str, Any], profile_name: str) -> list[dict[str, Any]]:
    path = case["metrics"]["postprocess"]["profiles"][profile_name]["path"]
    return read_profile_csv(path)


def validate_benchmark_matrix(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})

    required = [
        "baseline_wsl_v2112",
        "mesh_40x40_cfl_matched_wsl_v2112",
        "re100_wsl_v2112",
        "dt_half_wsl_v2112",
    ]
    for case_id in required:
        check(f"case.present.{case_id}", case_id in cases, case_id)
    if any(case_id not in cases for case_id in required):
        return {"passed": False, "gate": "integration", "checks": checks}

    for case_id, case in cases.items():
        check(
            f"case.{case_id}.runtime_validation",
            case["validation"].get("passed") is True,
            str(case["output_dir"]),
        )
        profiles = case["metrics"].get("postprocess", {}).get("profiles", {})
        for profile_name in ["vertical_centerline_Ux", "horizontal_centerline_Uy"]:
            profile = profiles.get(profile_name, {})
            path = Path(profile.get("path", ""))
            rows = read_profile_csv(path) if path.exists() else []
            check(f"case.{case_id}.profile.{profile_name}", len(rows) >= 3, str(path))

    baseline = cases["baseline_wsl_v2112"]
    mesh = cases["mesh_40x40_cfl_matched_wsl_v2112"]
    re100 = cases["re100_wsl_v2112"]
    dt_half = cases["dt_half_wsl_v2112"]

    base_v = _profile_rows(baseline, "vertical_centerline_Ux")
    mesh_v = _profile_rows(mesh, "vertical_centerline_Ux")
    dt_v = _profile_rows(dt_half, "vertical_centerline_Ux")
    base_h = _profile_rows(baseline, "horizontal_centerline_Uy")
    mesh_h = _profile_rows(mesh, "horizontal_centerline_Uy")
    dt_h = _profile_rows(dt_half, "horizontal_centerline_Uy")

    mesh_v_delta = _mean_abs_profile_delta(base_v, mesh_v, "Ux_m_s")
    mesh_h_delta = _mean_abs_profile_delta(base_h, mesh_h, "Uy_m_s")
    check(
        "trend.mesh_refinement.centerline_similarity",
        mesh_v_delta <= 0.08 and mesh_h_delta <= 0.08,
        f"vertical_Ux_MAE={mesh_v_delta:.6g}, horizontal_Uy_MAE={mesh_h_delta:.6g}, threshold=0.08",
    )

    dt_v_delta = _mean_abs_profile_delta(base_v, dt_v, "Ux_m_s")
    dt_h_delta = _mean_abs_profile_delta(base_h, dt_h, "Uy_m_s")
    base_courant = float(baseline["metrics"]["solver"]["max_courant_number"])
    dt_courant = float(dt_half["metrics"]["solver"]["max_courant_number"])
    check(
        "trend.dt_half.centerline_similarity_and_courant_drop",
        dt_v_delta <= 0.04 and dt_h_delta <= 0.04 and dt_courant < base_courant,
        f"vertical_Ux_MAE={dt_v_delta:.6g}, horizontal_Uy_MAE={dt_h_delta:.6g}, maxCo={dt_courant:.6g} < baseline {base_courant:.6g}",
    )

    mesh_v_stats = mesh["metrics"]["postprocess"]["profiles"]["vertical_centerline_Ux"]["stats"]
    re_v_stats = re100["metrics"]["postprocess"]["profiles"]["vertical_centerline_Ux"]["stats"]
    mesh_h_stats = mesh["metrics"]["postprocess"]["profiles"]["horizontal_centerline_Uy"]["stats"]
    re_h_stats = re100["metrics"]["postprocess"]["profiles"]["horizontal_centerline_Uy"]["stats"]
    re_vertical_gradient_ratio = float(re_v_stats["max_abs_dUx_m_s_dy_m"]) / max(float(mesh_v_stats["max_abs_dUx_m_s_dy_m"]), 1e-12)
    re_horizontal_gradient_ratio = float(re_h_stats["max_abs_dUy_m_s_dx_m"]) / max(float(mesh_h_stats["max_abs_dUy_m_s_dx_m"]), 1e-12)
    check(
        "trend.re100.stronger_velocity_gradients",
        re_vertical_gradient_ratio >= 1.05 and re_horizontal_gradient_ratio >= 1.05,
        f"vertical_gradient_ratio={re_vertical_gradient_ratio:.6g}, horizontal_gradient_ratio={re_horizontal_gradient_ratio:.6g}, threshold=1.05",
    )

    return {"passed": all(item["passed"] for item in checks), "gate": "integration", "checks": checks}


def _write_case_summary(cases: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "reynolds_number",
                "mesh_cells",
                "delta_t_s",
                "final_time",
                "max_courant_number",
                "vertical_Ux_range",
                "horizontal_Uy_range",
                "validation_passed",
            ],
        )
        writer.writeheader()
        for case_id, case in cases.items():
            config = case["config"]
            metrics = case["metrics"]
            writer.writerow(
                {
                    "case_id": case_id,
                    "reynolds_number": config["material"]["reynolds_number"],
                    "mesh_cells": "x".join(str(item) for item in config["mesh"]["cells"]),
                    "delta_t_s": config["numerics"]["control"]["delta_t_s"],
                    "final_time": metrics["solver"]["final_time"],
                    "max_courant_number": metrics["solver"]["max_courant_number"],
                    "vertical_Ux_range": metrics["postprocess"]["profiles"]["vertical_centerline_Ux"]["stats"]["Ux_m_s_range"],
                    "horizontal_Uy_range": metrics["postprocess"]["profiles"]["horizontal_centerline_Uy"]["stats"]["Uy_m_s_range"],
                    "validation_passed": case["validation"]["passed"],
                }
            )


def _write_plots(cases: dict[str, dict[str, Any]], plot_dir: Path) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_dir.mkdir(parents=True, exist_ok=True)
    vertical_path = plot_dir / "vertical_centerline_Ux_comparison.png"
    horizontal_path = plot_dir / "horizontal_centerline_Uy_comparison.png"

    plt.figure(figsize=(6, 4))
    for case_id, case in cases.items():
        rows = _profile_rows(case, "vertical_centerline_Ux")
        plt.plot([float(row["Ux_m_s"]) for row in rows], [float(row["y_over_L"]) for row in rows], label=case_id)
    plt.xlabel("Ux (m/s)")
    plt.ylabel("y / L")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(vertical_path, dpi=160)
    plt.close()

    plt.figure(figsize=(6, 4))
    for case_id, case in cases.items():
        rows = _profile_rows(case, "horizontal_centerline_Uy")
        plt.plot([float(row["x_over_L"]) for row in rows], [float(row["Uy_m_s"]) for row in rows], label=case_id)
    plt.xlabel("x / L")
    plt.ylabel("Uy (m/s)")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(horizontal_path, dpi=160)
    plt.close()
    return [str(vertical_path), str(horizontal_path)]


def _write_report(
    cases: dict[str, dict[str, Any]],
    validation: dict[str, Any],
    summary_csv: Path,
    plots: list[str],
    report_path: Path = REPORT_PATH,
) -> None:
    status = "passed" if validation["passed"] else "failed"
    failed = [item for item in validation["checks"] if not item["passed"]]
    lines = [
        "# OpenFOAM C01 benchmark validation report",
        "",
        "## Scope",
        "",
        "- capability: `C01_lid_driven_cavity_incompressible_laminar`",
        "- gate: `integration`",
        f"- matrix status: `{status}`",
        "- runtime profile: `openfoam_com_v2112`",
        "- WSL distro: `Ubuntu-24.04`",
        f"- benchmark summary: `{summary_csv}`",
        "",
        "## Case Matrix",
        "",
    ]
    for case_id, case in cases.items():
        config = case["config"]
        metrics = case["metrics"]
        lines.append(
            f"- `{case_id}`: Re={config['material']['reynolds_number']}, mesh={config['mesh']['cells']}, "
            f"dt={config['numerics']['control']['delta_t_s']}, maxCo={metrics['solver']['max_courant_number']}, "
            f"validation={case['validation']['passed']}"
        )
    lines.extend(["", "## Trend Checks", ""])
    for item in validation["checks"]:
        if item["name"].startswith("trend."):
            mark = "passed" if item["passed"] else "failed"
            lines.append(f"- `{item['name']}`: {mark}; {item['details']}")
    lines.extend(["", "## Numeric Artifacts", "", f"- case summary CSV: `{summary_csv}`"])
    for plot in plots:
        lines.append(f"- plot: `{plot}`")
    lines.extend(["", "## Status Conclusion", ""])
    if validation["passed"]:
        lines.append("The four-case matrix, solver health checks, centerline CSV artifacts, trend checks, and plots passed. This supports promoting `benchmark_status` to `benchmark_validated`.")
    else:
        lines.append("The matrix validation did not fully pass. Do not promote `benchmark_status`.")
        for item in failed:
            lines.append(f"- failed `{item['name']}`: {item['details']}")
    lines.extend([
        "",
        "## Residual Risk",
        "",
        "- Evidence is from local WSL OpenFOAM.com v2112 only; Foundation OpenFOAM is not covered by this report.",
        "- Trend checks are based on official tutorial physics and local perturbations, not on an external high-accuracy Ghia-style reference dataset.",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_benchmark_matrix(config_paths: list[Path] | None = None) -> dict[str, Any]:
    paths = config_paths or DEFAULT_CONFIGS
    for path in paths:
        result = run(config_path=path)
        if not result.get("validation", {}).get("passed", False):
            break
    cases = {}
    for path in paths:
        loaded = _load_metrics_for_config(path)
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
