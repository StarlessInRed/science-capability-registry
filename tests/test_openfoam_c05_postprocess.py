from __future__ import annotations

import csv
import math
from pathlib import Path

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.postprocess import (
    estimate_strouhal,
    read_force_coefficients,
    write_force_metrics,
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


def test_openfoam_c05_strouhal_records_fft_cross_check() -> None:
    frequency_hz = 0.5
    rows = [
        {
            "time_s": index * 0.05,
            "cm": 0.0,
            "cd": 1.0,
            "cl": math.sin(2.0 * math.pi * frequency_hz * index * 0.05),
        }
        for index in range(161)
    ]

    strouhal = estimate_strouhal(
        rows,
        cylinder_diameter_m=1.0,
        inlet_velocity_m_s=1.0,
        min_lift_peaks=3,
        strouhal_estimation_method="lift_peak_period",
        frequency_cross_checks=["lift_fft"],
        force_extraction_source="python_patch_surface_proxy",
    )

    estimates = {estimate["method"]: estimate for estimate in strouhal["frequency_estimates"]}
    assert strouhal["available"] is True
    assert strouhal["selected_method"] == "lift_peak_period"
    assert strouhal["source"] == "force_coefficients.cl"
    assert strouhal["force_extraction_source"] == "python_patch_surface_proxy"
    assert estimates["lift_fft"]["available"] is True
    assert abs(estimates["lift_fft"]["strouhal_number"] - strouhal["strouhal_number"]) / strouhal["strouhal_number"] < 0.05


def test_openfoam_c05_python_patch_surface_proxy_writes_force_csv(tmp_path: Path) -> None:
    case_dir = tmp_path / "case"
    mesh_dir = case_dir / "constant" / "polyMesh"
    mesh_dir.mkdir(parents=True)
    (case_dir / "1").mkdir(parents=True)
    (mesh_dir / "points").write_text(
        """
FoamFile{}
8
(
(0 0 0)
(1 0 0)
(1 1 0)
(0 1 0)
(0 0 1)
(1 0 1)
(1 1 1)
(0 1 1)
)
""",
        encoding="utf-8",
    )
    (mesh_dir / "faces").write_text(
        """
FoamFile{}
6
(
4(1 5 6 2)
4(0 3 7 4)
4(0 4 5 1)
4(3 2 6 7)
4(0 1 2 3)
4(4 7 6 5)
)
""",
        encoding="utf-8",
    )
    (mesh_dir / "owner").write_text("FoamFile{}\n6\n(\n0\n0\n0\n0\n0\n0\n)\n", encoding="utf-8")
    (mesh_dir / "neighbour").write_text("FoamFile{}\n0\n(\n)\n", encoding="utf-8")
    (mesh_dir / "boundary").write_text(
        """
FoamFile{}
2
(
cylinder
{
    type wall;
    nFaces 1;
    startFace 0;
}
other
{
    type patch;
    nFaces 5;
    startFace 1;
}
)
""",
        encoding="utf-8",
    )
    (case_dir / "1" / "p").write_text(
        """
FoamFile{}
internalField nonuniform List<scalar>
1
(
2
)
;
""",
        encoding="utf-8",
    )
    (case_dir / "1" / "U").write_text(
        """
FoamFile{}
internalField nonuniform List<vector>
1
(
(1 0 0)
)
;
""",
        encoding="utf-8",
    )
    config = {
        "geometry": {"cylinder_diameter_m": 1.0, "two_dimensional_thickness_m": 1.0, "cylinder_center_m": [0.0, 0.0]},
        "material": {"density_kg_m3": 1.0, "kinematic_viscosity_m2_s": 0.0, "inlet_velocity_m_s": 2.0},
        "function_objects": {
            "force_coefficients": {
                "patches": ["cylinder"],
                "lift_dir": [0.0, 1.0, 0.0],
                "drag_dir": [1.0, 0.0, 0.0],
            }
        },
        "postprocess": {"force_extraction_source": "python_patch_surface_proxy"},
    }

    result = write_force_metrics(config, tmp_path)

    assert result["force_coefficients"]["available"] is True
    assert result["force_coefficients"]["source"] == "python_patch_surface_proxy"
    assert result["force_coefficients"]["row_count"] == 1
    with (tmp_path / "postprocess" / "force_coefficients.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert float(rows[0]["cd"]) == 1.0
