from __future__ import annotations

from pathlib import Path

from science_capability_registry.comsol.matlab_server_bridge_runtime.validation import (
    parse_scalar_file,
    summarize_environment_checks,
)


def test_parse_scalar_file_accepts_finite_value(tmp_path: Path) -> None:
    scalar_path = tmp_path / "comsol_c01_scalar.txt"
    scalar_path.write_text("bridge_scalar=1.25\n", encoding="utf-8")

    assert parse_scalar_file(scalar_path, "bridge_scalar") == 1.25


def test_parse_scalar_file_rejects_nonfinite_value(tmp_path: Path) -> None:
    scalar_path = tmp_path / "comsol_c01_scalar.txt"
    scalar_path.write_text("bridge_scalar=nan\n", encoding="utf-8")

    assert parse_scalar_file(scalar_path, "bridge_scalar") is None


def test_summarize_environment_checks_counts_required_paths() -> None:
    checks = [
        {"env": "MATLAB_EXE", "required": True, "configured": True, "exists": True},
        {"env": "COMSOL_BIN", "required": True, "configured": True, "exists": False},
        {"env": "COMSOL_MLI_DIR", "required": True, "configured": False, "exists": False},
        {"env": "COMSOL_MPHSERVER_BIN", "required": False, "configured": True, "exists": True},
    ]

    summary = summarize_environment_checks(checks)

    assert summary["required_count"] == 3
    assert summary["required_configured_count"] == 2
    assert summary["required_existing_count"] == 1
    assert summary["optional_configured_count"] == 1
    assert summary["all_required_configured"] is False
    assert summary["all_required_paths_exist"] is False
