from __future__ import annotations

import math
from pathlib import Path

from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.config import load_case_config
from science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.postprocess import (
    read_y_plus_log,
    read_force_coefficients,
    summarize_force_tail,
    summarize_y_plus,
    write_force_metrics,
    write_y_plus_summary,
)


def test_openfoam_c04_reads_and_summarizes_force_coefficients(tmp_path: Path) -> None:
    path = tmp_path / "coefficient.dat"
    path.write_text("# Time Cm Cd Cl\n400 0.01 0.30 0.05\n500 0.02 0.32 0.06\n", encoding="utf-8")
    rows = read_force_coefficients(path)
    summary = summarize_force_tail(rows, 2)

    assert len(rows) == 2
    assert math.isclose(summary["cd_tail_mean"], 0.31)
    assert summary["cl_tail_std"] > 0.0


def test_openfoam_c04_yplus_summary_tracks_range(tmp_path: Path) -> None:
    rows = [
        {"patch": "motorBikeGroup", "sample_count": 10, "min": 40.0, "max": 120.0, "mean": 80.0},
        {"patch": "lowerWall", "sample_count": 5, "min": 35.0, "max": 90.0, "mean": 70.0},
    ]
    summary = write_y_plus_summary(rows, tmp_path / "yplus_summary.csv")

    assert summary["available"] is True
    assert summary["sample_count"] == 15
    assert summary["min"] == 35.0
    assert summary["max"] == 120.0


def test_openfoam_c04_reads_yplus_log_summary(tmp_path: Path) -> None:
    log_path = tmp_path / "log.yPlus"
    log_path.write_text(
        "patch motorBikeGroup y+ : min = 40 max = 120 average = 80\n"
        "patch lowerWall y+ : min = 35 max = 90 mean = 70\n",
        encoding="utf-8",
    )

    rows = read_y_plus_log(log_path)
    summary = summarize_y_plus(rows)

    assert len(rows) == 2
    assert summary["available"] is True
    assert summary["min"] == 35.0
    assert summary["max"] == 120.0


def test_openfoam_c04_write_force_metrics_accepts_synthetic_rows(tmp_path: Path) -> None:
    config = load_case_config("configs/openfoam/external_aero_motorbike_rans_snappy/baseline.yaml")
    metrics = write_force_metrics(
        config,
        tmp_path,
        [
            {"iteration": 300.0, "cm": 0.0, "cd": 0.31, "cl": 0.05},
            {"iteration": 400.0, "cm": 0.0, "cd": 0.32, "cl": 0.05},
            {"iteration": 500.0, "cm": 0.0, "cd": 0.315, "cl": 0.05},
        ],
    )

    assert metrics["available"] is True
    assert Path(metrics["path"]).exists()
    assert Path(metrics["summary_path"]).exists()


def test_openfoam_c04_yplus_summary_detects_nonfinite() -> None:
    summary = summarize_y_plus([{"patch": "motorBikeGroup", "sample_count": 1, "min": 40.0, "max": math.nan, "mean": 80.0}])

    assert summary["available"] is False
    assert summary["finite_patch_count"] == 0
