from __future__ import annotations

import pytest

from science_capability_registry.cantera.c05_reaction_path_analysis.postprocess import (
    parse_reaction_path_data,
)


def test_parse_reaction_path_data_skips_optional_title_line() -> None:
    data = """
Reaction path diagram following N
N N2 NO NNH HCN
N N2 1.0e-9 -2.0e-9
N2 NNH 2.7e-2 -2.6e-2
"""
    nodes, edges = parse_reaction_path_data(data)
    assert nodes == ["N", "N2", "NO", "NNH", "HCN"]
    assert edges[0]["source"] == "N"
    assert edges[0]["target"] == "N2"
    assert edges[1]["abs_net_flux"] == pytest.approx(1.0e-3)


def test_parse_reaction_path_data_rejects_malformed_edge_rows() -> None:
    data = """
N N2 NO
N N2 1.0e-9 -2.0e-9
malformed row
"""
    with pytest.raises(ValueError):
        parse_reaction_path_data(data)
