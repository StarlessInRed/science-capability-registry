"""Runner for the Cantera C05 reaction path analysis capability."""

from __future__ import annotations

import contextlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .postprocess import (
    parse_reaction_path_data,
    plot_flux_summary,
    summarize_paths,
    write_data_txt,
    write_edges_csv,
)
from .report import write_validation_report
from .validation import validate_metrics


def _import_solver_stack() -> tuple[Any, Any]:
    try:
        import cantera as ct
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Cantera is required to execute this capability. Install cantera>=3.2 "
            "in the active environment, then rerun the C05 case."
        ) from exc

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return ct, plt


def _run_reactor_to_target(ct: Any, config: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    gas = ct.Solution(config["mechanism"])
    gas.TPX = (
        float(config["initial_temperature_k"]),
        float(config["pressure_pa"]),
        config["composition"],
    )
    gas.element_index(config["element"])

    reactor = ct.IdealGasReactor(gas, clone=False)
    network = ct.ReactorNet([reactor])
    target_temperature = float(config["target_temperature_k"])
    max_time = float(config["max_time_s"])
    max_steps = int(config["max_steps"])
    step_count = 0

    print(f"{'step':>8s} {'t [s]':>12s} {'T [K]':>12s} {'P [Pa]':>12s}")
    print(f"{step_count:8d} {network.time:12.6e} {reactor.T:12.6f} {reactor.phase.P:12.6f}")
    while reactor.T < target_temperature:
        network.step()
        step_count += 1
        if step_count % 100 == 0 or reactor.T >= target_temperature:
            print(
                f"{step_count:8d} {network.time:12.6e} "
                f"{reactor.T:12.6f} {reactor.phase.P:12.6f}"
            )
        if network.time > max_time:
            raise RuntimeError(
                f"C05 reactor exceeded max_time_s={max_time} before reaching "
                f"target_temperature_k={target_temperature}."
            )
        if step_count >= max_steps:
            raise RuntimeError(
                f"C05 reactor exceeded max_steps={max_steps} before reaching "
                f"target_temperature_k={target_temperature}."
            )

    state = {
        "final_temperature_k": float(reactor.T),
        "final_pressure_pa": float(reactor.phase.P),
        "final_time_s": float(network.time),
        "step_count": int(step_count),
    }
    return gas, state


def _build_diagram(ct: Any, gas: Any, config: dict[str, Any]) -> Any:
    diagram = ct.ReactionPathDiagram(gas, config["element"])
    diagram.title = config["diagram"]["title"]
    diagram.label_threshold = float(config["diagram"]["label_threshold"])
    return diagram


def _render_graph_png(dot_path: Path, png_path: Path) -> None:
    dot_executable = shutil.which("dot")
    if dot_executable is None:
        raise RuntimeError(
            "Graphviz 'dot' was requested by outputs.save_graph_png=true, "
            "but it is not available on PATH."
        )
    subprocess.run(
        [dot_executable, str(dot_path), "-Tpng", f"-o{png_path}"],
        check=True,
        capture_output=True,
        text=True,
    )


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run or dry-run the C05 reaction path analysis capability."""
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)

    resolved_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else repo_relative_path(config["outputs"]["output_dir"])
    )

    if dry_run:
        return {
            "capability_id": config["capability_id"],
            "case_id": config["case_id"],
            "output_dir": str(resolved_output_dir),
            "validated_config": True,
            "requires_solver": "cantera>=3.2",
            "requires_renderer": "matplotlib; graphviz dot optional for external DOT rendering",
        }

    ct, plt = _import_solver_stack()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    log_path = resolved_output_dir / "reaction_path_run.log"
    dot_path = resolved_output_dir / "reaction_path.dot"
    graph_png_path = resolved_output_dir / "reaction_path_graph.png"
    data_path = resolved_output_dir / "reaction_path_data.txt"
    csv_path = resolved_output_dir / "reaction_path_edges.csv"
    plot_path = resolved_output_dir / "reaction_path_top_fluxes.png"
    metrics_path = resolved_output_dir / "metrics.json"
    report_path = resolved_output_dir / "validation_report.md"

    with log_path.open("w", encoding="utf-8") as log_handle:
        with contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
            print(f"Running {config['capability_id']} case {config['case_id']}")
            print(f"Cantera version: {ct.__version__}")
            gas, reactor_state = _run_reactor_to_target(ct, config)
            diagram = _build_diagram(ct, gas, config)
            data = diagram.get_data()
            dot = diagram.get_dot()
            print(f"Reaction path element: {config['element']}")
            print(f"Reaction path data bytes: {len(data.encode('utf-8'))}")

    nodes, edges = parse_reaction_path_data(data)
    path_summary = summarize_paths(
        nodes,
        edges,
        significant_flux_threshold=float(config["validation"]["significant_flux_threshold"]),
    )

    artifacts: dict[str, str] = {}
    if config["outputs"]["save_dot"]:
        dot_path.write_text(dot, encoding="utf-8")
        artifacts["reaction_path.dot"] = str(dot_path)
    if config["outputs"]["save_graph_png"]:
        if not dot_path.exists():
            dot_path.write_text(dot, encoding="utf-8")
        _render_graph_png(dot_path, graph_png_path)
        artifacts["reaction_path_graph.png"] = str(graph_png_path)
    if config["outputs"]["save_data_txt"]:
        write_data_txt(data_path, data)
        artifacts["reaction_path_data.txt"] = str(data_path)
    if config["outputs"]["save_csv"]:
        write_edges_csv(csv_path, edges)
        artifacts["reaction_path_edges.csv"] = str(csv_path)
    if config["outputs"]["save_flux_plot"]:
        plot_flux_summary(plt, path_summary, plot_path)
        artifacts["reaction_path_top_fluxes.png"] = str(plot_path)
    if config["outputs"]["save_log"]:
        artifacts["reaction_path_run.log"] = str(log_path)

    metrics: dict[str, Any] = {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "cantera_version": ct.__version__,
        "mechanism": config["mechanism"],
        "element": config["element"],
        "label_threshold": float(config["diagram"]["label_threshold"]),
        "reactor_state": reactor_state,
        "nodes": nodes,
        "path_summary": path_summary,
        "artifacts": artifacts,
    }
    if config["outputs"]["save_metrics"]:
        metrics["artifacts"]["metrics.json"] = str(metrics_path)
    if config["outputs"]["save_validation_report"]:
        metrics["artifacts"]["validation_report.md"] = str(report_path)

    pending_validation = {
        "passed": False,
        "checks": [
            {
                "name": "validation.pending",
                "passed": False,
                "details": "Final validation has not been calculated yet.",
            }
        ],
    }
    metrics["validation"] = pending_validation
    if config["outputs"]["save_metrics"]:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if config["outputs"]["save_validation_report"]:
        write_validation_report(report_path, config, metrics, pending_validation)

    validation = validate_metrics(metrics, config, resolved_output_dir)
    metrics["validation"] = validation

    if config["outputs"]["save_metrics"]:
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if config["outputs"]["save_validation_report"]:
        write_validation_report(report_path, config, metrics, validation)

    return metrics


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Stable package entrypoint for external workflow callers."""
    return run(config_path=config_path, output_dir=output_dir)
