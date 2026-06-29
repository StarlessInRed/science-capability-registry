"""Automatic validation for Cantera C05 outputs."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _in_range(value: float, limits: dict[str, float]) -> bool:
    return float(limits["min"]) <= value <= float(limits["max"])


def _expected_artifacts(config: dict[str, Any]) -> list[str]:
    outputs = config["outputs"]
    expected: list[str] = []
    if outputs["save_dot"]:
        expected.append("reaction_path.dot")
    if outputs["save_graph_png"]:
        expected.append("reaction_path_graph.png")
    if outputs["save_data_txt"]:
        expected.append("reaction_path_data.txt")
    if outputs["save_csv"]:
        expected.append("reaction_path_edges.csv")
    if outputs["save_flux_plot"]:
        expected.append("reaction_path_top_fluxes.png")
    if outputs["save_log"]:
        expected.append("reaction_path_run.log")
    if outputs["save_metrics"]:
        expected.append("metrics.json")
    if outputs["save_validation_report"]:
        expected.append("validation_report.md")
    return expected


def validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    limits = config["validation"]
    state = metrics.get("reactor_state", {})
    summary = metrics.get("path_summary", {})
    nodes = metrics.get("nodes", [])

    final_temperature = float(state.get("final_temperature_k", math.nan))
    final_time = float(state.get("final_time_s", math.nan))
    step_count = int(state.get("step_count", 0))

    _check(
        checks,
        "reactor.target_temperature_reached",
        math.isfinite(final_temperature) and final_temperature >= float(config["target_temperature_k"]),
        f"Final temperature is {final_temperature:.6g} K.",
    )
    _check(
        checks,
        "reactor.final_temperature_reference_range",
        _in_range(final_temperature, limits["final_temperature_k"]),
        (
            f"Expected {limits['final_temperature_k']['min']} K <= final <= "
            f"{limits['final_temperature_k']['max']} K; got {final_temperature:.6g} K."
        ),
    )
    _check(
        checks,
        "reactor.final_time",
        math.isfinite(final_time) and final_time <= float(limits["max_final_time_s"]),
        f"Final time is {final_time:.6g} s.",
    )
    _check(
        checks,
        "reactor.step_count",
        step_count >= int(limits["min_step_count"]) and step_count <= int(config["max_steps"]),
        f"Step count is {step_count}.",
    )
    _check(
        checks,
        "diagram.element_recorded",
        metrics.get("element") == config["element"],
        f"Metrics element is {metrics.get('element')}.",
    )
    _check(
        checks,
        "diagram.label_threshold_recorded",
        float(metrics.get("label_threshold", math.nan))
        == float(config["diagram"]["label_threshold"]),
        f"Label threshold is {metrics.get('label_threshold')}.",
    )
    _check(
        checks,
        "diagram.nodes",
        int(summary.get("node_count", 0)) >= int(limits["min_node_count"]),
        f"Node count is {summary.get('node_count')}.",
    )
    _check(
        checks,
        "diagram.edges",
        int(summary.get("edge_count", 0)) >= int(limits["min_edge_count"]),
        f"Nonzero edge count is {summary.get('edge_count')}.",
    )
    _check(
        checks,
        "diagram.significant_edges",
        int(summary.get("significant_edge_count", 0))
        >= int(limits["min_significant_edge_count"]),
        f"Significant edge count is {summary.get('significant_edge_count')}.",
    )
    max_abs_net_flux = float(summary.get("max_abs_net_flux", math.nan))
    _check(
        checks,
        "diagram.max_abs_net_flux",
        math.isfinite(max_abs_net_flux) and max_abs_net_flux >= float(limits["min_max_abs_net_flux"]),
        f"Maximum absolute net flux is {max_abs_net_flux:.6g}.",
    )

    top_edges = summary.get("top_edges", [])
    finite_edges = all(
        math.isfinite(float(edge.get("forward_flux", math.nan)))
        and math.isfinite(float(edge.get("reverse_flux", math.nan)))
        and math.isfinite(float(edge.get("net_flux", math.nan)))
        for edge in top_edges
    )
    _check(checks, "diagram.top_edges_finite", finite_edges, "Top edge fluxes are finite.")

    element = str(config["element"])
    element_nodes = [node for node in nodes if element in str(node)]
    _check(
        checks,
        "diagram.element_nodes_present",
        len(element_nodes) >= int(limits["min_node_count"]),
        f"Nodes containing element token {element}: {len(element_nodes)}.",
    )
    expected_nodes = list(config["validation"]["expected_nodes"])
    missing_nodes = [node for node in expected_nodes if node not in nodes]
    _check(
        checks,
        "diagram.expected_nodes",
        not missing_nodes,
        f"Missing expected nodes: {missing_nodes}.",
    )

    if output_dir is not None:
        artifacts = metrics.get("artifacts", {})
        for artifact_name in _expected_artifacts(config):
            artifact_path = artifacts.get(artifact_name)
            path = Path(artifact_path) if artifact_path else Path(output_dir) / artifact_name
            if not path.is_absolute():
                path = Path(output_dir) / path
            exists = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.{artifact_name}", exists, f"Artifact path: {path}")
            if exists and artifact_name == "reaction_path.dot":
                text = path.read_text(encoding="utf-8", errors="replace")
                dot_valid = "digraph" in text and str(config["element"]) in text
                _check(
                    checks,
                    "artifact.reaction_path.dot_content",
                    dot_valid,
                    "DOT contains digraph and target element evidence.",
                )
            if exists and artifact_name == "reaction_path_graph.png":
                with path.open("rb") as handle:
                    signature = handle.read(8)
                _check(
                    checks,
                    "artifact.reaction_path_graph.png_signature",
                    signature == b"\x89PNG\r\n\x1a\n",
                    "Graph PNG has a valid PNG signature.",
                )

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
