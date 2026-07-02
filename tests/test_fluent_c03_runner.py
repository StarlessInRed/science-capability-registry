from __future__ import annotations

import csv
import json
from pathlib import Path

from science_capability_registry.fluent.mesh_convergence_trend.runner import run


def test_fluent_c03_runner_writes_trend_contract(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validation"]["passed"] is True
    assert result["metrics"]["mesh_level_count"] == 3
    assert result["metrics"]["cell_counts_strictly_increasing"] is True
    for rel_path in [
        "trend_contract.json",
        "refinement_matrix.csv",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]:
        assert (tmp_path / rel_path).exists()

    contract = json.loads((tmp_path / "trend_contract.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((tmp_path / "refinement_matrix.csv").read_text(encoding="utf-8").splitlines()))

    assert contract["mesh_levels"][1]["level_id"] == "baseline"
    assert [row["level_id"] for row in rows] == ["coarse", "baseline", "refined"]


def test_fluent_c03_runner_rejects_non_dry_run(tmp_path: Path) -> None:
    try:
        run(
            config_path=Path("configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml"),
            output_dir=tmp_path,
            dry_run=False,
        )
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C03 non-dry-run rejection")

