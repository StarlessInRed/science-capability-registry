from __future__ import annotations

from pathlib import Path

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.postprocess import (
    estimate_strouhal,
    read_force_coefficients,
    write_force_coefficients_csv,
)


def test_openfoam_c05_force_coefficients_and_strouhal(tmp_path: Path) -> None:
    source = tmp_path / "coefficient.dat"
    source.write_text(
        "\n".join(
            [
                "# Time Cm Cd Cl",
                "0.0 0 1.0 0.0",
                "0.5 0 1.1 1.0",
                "1.0 0 1.0 0.0",
                "1.5 0 1.1 1.0",
                "2.0 0 1.0 0.0",
                "2.5 0 1.1 1.0",
                "3.0 0 1.0 0.0",
            ]
        ),
        encoding="utf-8",
    )

    rows = read_force_coefficients(source)
    csv_info = write_force_coefficients_csv(rows, tmp_path / "force_coefficients.csv")
    strouhal = estimate_strouhal(rows, cylinder_diameter_m=1.0, inlet_velocity_m_s=1.0)

    assert csv_info["row_count"] == 7
    assert strouhal["available"] is True
    assert strouhal["strouhal_number"] == 1.0


def test_openfoam_c05_strouhal_requires_lift_peaks() -> None:
    rows = [{"time_s": float(index), "cm": 0.0, "cd": 1.0, "cl": 0.0} for index in range(5)]

    strouhal = estimate_strouhal(rows, cylinder_diameter_m=1.0, inlet_velocity_m_s=1.0)

    assert strouhal["available"] is False
