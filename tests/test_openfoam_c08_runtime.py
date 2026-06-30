from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.compressible_shock_capturing_forward_step.runtime import (
    _read_final_fields,
    parse_rhocentralfoam_log,
)


def test_openfoam_c08_parse_rhocentralfoam_v2112_courant_format() -> None:
    metrics = parse_rhocentralfoam_log(
        """
Mean and max Courant Numbers = 0.66643 0.666666
Time = 0.00238095
Mean and max Courant Numbers = 0.153695 0.203395
Time = 4
End
"""
    )

    assert metrics["started"] is True
    assert metrics["fatal_error_detected"] is False
    assert metrics["final_time_s"] == 4.0
    assert metrics["max_courant"] == 0.666666


def test_openfoam_c08_read_final_fields_from_latest_time(tmp_path: Path) -> None:
    time_dir = tmp_path / "case" / "4"
    time_dir.mkdir(parents=True)
    (time_dir / "p").write_text("internalField uniform 1;\n", encoding="utf-8")
    (time_dir / "T").write_text("internalField uniform 2;\n", encoding="utf-8")
    (time_dir / "rho").write_text("internalField uniform 3;\n", encoding="utf-8")
    (time_dir / "U").write_text("internalField uniform (1 0 0);\n", encoding="utf-8")

    fields = _read_final_fields(tmp_path / "case")

    assert fields["p"] == [1.0]
    assert fields["T"] == [2.0]
    assert fields["rho"] == [3.0]
    assert fields["U"] == [(1.0, 0.0, 0.0)]
