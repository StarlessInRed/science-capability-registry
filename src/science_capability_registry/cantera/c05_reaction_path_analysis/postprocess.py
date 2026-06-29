"""Reaction path data parsing and artifact writers for Cantera C05."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def parse_reaction_path_data(data: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Parse Cantera ReactionPathDiagram.get_data() output."""
    lines = [line.strip() for line in data.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Reaction path data must include a node header and edge rows.")

    first_edge_index = -1
    for index, line in enumerate(lines):
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            float(parts[2])
            float(parts[3])
        except ValueError:
            continue
        first_edge_index = index
        break

    if first_edge_index <= 0:
        raise ValueError("Could not locate reaction path edge rows after a node header.")

    nodes = lines[first_edge_index - 1].split()
    if not nodes:
        raise ValueError("Reaction path node header is empty.")

    edges: list[dict[str, Any]] = []
    for line in lines[first_edge_index:]:
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Malformed reaction path edge row: {line}")
        source, target, forward_text, reverse_text = parts
        forward_flux = float(forward_text)
        reverse_flux = float(reverse_text)
        net_flux = forward_flux + reverse_flux
        edges.append(
            {
                "source": source,
                "target": target,
                "forward_flux": forward_flux,
                "reverse_flux": reverse_flux,
                "net_flux": net_flux,
                "abs_net_flux": abs(net_flux),
                "max_directional_flux": max(abs(forward_flux), abs(reverse_flux)),
            }
        )
    return nodes, edges


def summarize_paths(
    nodes: list[str],
    edges: list[dict[str, Any]],
    significant_flux_threshold: float,
    top_edge_count: int = 12,
) -> dict[str, Any]:
    nonzero_edges = [
        edge
        for edge in edges
        if edge["max_directional_flux"] > 0.0 or edge["abs_net_flux"] > 0.0
    ]
    significant_edges = [
        edge for edge in nonzero_edges if edge["abs_net_flux"] >= significant_flux_threshold
    ]
    sorted_edges = sorted(nonzero_edges, key=lambda edge: edge["abs_net_flux"], reverse=True)
    max_abs_net_flux = sorted_edges[0]["abs_net_flux"] if sorted_edges else math.nan
    return {
        "node_count": len(nodes),
        "edge_count": len(nonzero_edges),
        "parsed_edge_count": len(edges),
        "significant_edge_count": len(significant_edges),
        "significant_flux_threshold": float(significant_flux_threshold),
        "max_abs_net_flux": float(max_abs_net_flux),
        "total_forward_flux": float(sum(abs(edge["forward_flux"]) for edge in nonzero_edges)),
        "total_reverse_flux": float(sum(abs(edge["reverse_flux"]) for edge in nonzero_edges)),
        "top_edges": sorted_edges[:top_edge_count],
    }


def write_edges_csv(path: str | Path, edges: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "target",
        "forward_flux",
        "reverse_flux",
        "net_flux",
        "abs_net_flux",
        "max_directional_flux",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(edges)


def write_data_txt(path: str | Path, data: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(data, encoding="utf-8")


def plot_flux_summary(plt: Any, summary: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    top_edges = summary.get("top_edges", [])
    labels = [f"{edge['source']}->{edge['target']}" for edge in top_edges]
    values = [edge["abs_net_flux"] for edge in top_edges]

    fig, ax = plt.subplots(figsize=(8, max(4, 0.35 * max(1, len(labels)))))
    positions = list(range(len(labels)))
    ax.barh(positions, values)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("absolute net flux")
    ax.set_title("Top reaction-path fluxes")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
