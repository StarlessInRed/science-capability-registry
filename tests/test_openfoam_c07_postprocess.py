from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.postprocess import (
    write_interface_balance_summary,
    write_patch_heat_flux_proxy_summary,
    write_region_temperature_summary,
)


def _config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml").read_text(
            encoding="utf-8"
        )
    )


def _mhr_config() -> dict:
    return yaml.safe_load(
        Path(
            "configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml"
        ).read_text(encoding="utf-8")
    )


def _write_scalar_field(path: Path, values: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"{value:g}" for value in values)
    path.write_text(
        f"""FoamFile
{{
    version 2.0;
    format ascii;
    class volScalarField;
    object T;
}}
dimensions [0 0 0 1 0 0 0];
internalField nonuniform List<scalar>
{len(values)}
(
{body}
)
;
boundaryField {{}}
""",
        encoding="utf-8",
    )


def _write_uniform_scalar_field(path: Path, value: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""FoamFile
{{
    version 2.0;
    format ascii;
    class volScalarField;
    object T;
}}
dimensions [0 0 0 1 0 0 0];
internalField uniform {value:g};
boundaryField {{}}
""",
        encoding="utf-8",
    )


def _write_single_cell_region_mesh(poly_dir: Path, x0: float, x1: float, interface_patch: str, interface_at_max_x: bool) -> None:
    poly_dir.mkdir(parents=True, exist_ok=True)
    points = [
        (x0, 0.0, 0.0),
        (x1, 0.0, 0.0),
        (x1, 1.0, 0.0),
        (x0, 1.0, 0.0),
        (x0, 0.0, 1.0),
        (x1, 0.0, 1.0),
        (x1, 1.0, 1.0),
        (x0, 1.0, 1.0),
    ]
    faces = [
        [0, 4, 7, 3],
        [1, 2, 6, 5],
        [0, 1, 5, 4],
        [3, 7, 6, 2],
        [0, 3, 2, 1],
        [4, 5, 6, 7],
    ]
    interface_index = 1 if interface_at_max_x else 0
    other_faces = [index for index in range(len(faces)) if index != interface_index]
    ordered_faces = [faces[interface_index], *[faces[index] for index in other_faces]]
    poly_dir.joinpath("points").write_text(
        "8\n(\n" + "\n".join(f"({x:g} {y:g} {z:g})" for x, y, z in points) + "\n)\n",
        encoding="utf-8",
    )
    poly_dir.joinpath("faces").write_text(
        "6\n(\n" + "\n".join(f"{len(face)}(" + " ".join(str(item) for item in face) + ")" for face in ordered_faces) + "\n)\n",
        encoding="utf-8",
    )
    poly_dir.joinpath("owner").write_text("6\n(\n0\n0\n0\n0\n0\n0\n)\n", encoding="utf-8")
    poly_dir.joinpath("neighbour").write_text("0\n(\n)\n", encoding="utf-8")
    poly_dir.joinpath("boundary").write_text(
        f"""2
(
    {interface_patch}
    {{
        type patch;
        nFaces 1;
        startFace 0;
    }}
    walls
    {{
        type wall;
        nFaces 5;
        startFace 1;
    }}
)
""",
        encoding="utf-8",
    )


def test_write_region_temperature_and_interface_summaries(tmp_path: Path) -> None:
    config = _config()
    _write_scalar_field(tmp_path / "case" / "200" / "domain0" / "T", [300.0, 310.0, 320.0])
    _write_scalar_field(tmp_path / "case" / "200" / "v_CPU" / "T", [330.0, 340.0])
    _write_scalar_field(tmp_path / "case" / "200" / "v_fins" / "T", [315.0, 325.0])

    temperatures = write_region_temperature_summary(config, tmp_path, final_time=200.0)
    interfaces = write_interface_balance_summary(config, tmp_path, temperatures)

    assert Path(temperatures["csv"]).exists()
    assert Path(interfaces["csv"]).exists()
    assert temperatures["available"] is True
    assert len(temperatures["regions"]) == 3
    assert interfaces["available"] is True
    assert interfaces["interfaces"][0]["mean_abs_delta_T_K"] == 25.0


def test_write_heater_radiation_temperature_summaries(tmp_path: Path) -> None:
    config = _mhr_config()
    _write_scalar_field(tmp_path / "case" / "2" / "bottomAir" / "T", [300.0, 380.0])
    _write_scalar_field(tmp_path / "case" / "2" / "topAir" / "T", [300.0, 300.1])
    _write_scalar_field(tmp_path / "case" / "2" / "heater" / "T", [500.0])
    _write_scalar_field(tmp_path / "case" / "2" / "leftSolid" / "T", [300.0, 300.05])
    _write_scalar_field(tmp_path / "case" / "2" / "rightSolid" / "T", [300.0, 300.1])

    temperatures = write_region_temperature_summary(config, tmp_path, final_time=2.0)
    interfaces = write_interface_balance_summary(config, tmp_path, temperatures)

    assert temperatures["available"] is True
    assert len(temperatures["regions"]) == 5
    assert interfaces["available"] is True
    assert {row["interface"] for row in interfaces["interfaces"]} == {
        "bottomAir_to_heater",
        "topAir_to_heater",
        "heater_to_leftSolid",
        "heater_to_rightSolid",
    }


def test_write_patch_heat_flux_proxy_summary_from_region_patch_meshes(tmp_path: Path) -> None:
    config = _mhr_config()
    config["regions"] = {"fluid": ["bottomAir"], "solid": ["heater"]}
    config["interfaces"] = [
        {
            "name": "bottomAir_to_heater",
            "owner_region": "bottomAir",
            "neighbour_region": "heater",
            "owner_patch": "bottomAir_to_heater",
            "neighbour_patch": "heater_to_bottomAir",
            "temperature_bc": "compressible::turbulentTemperatureRadCoupledMixed",
        }
    ]
    _write_single_cell_region_mesh(
        tmp_path / "case" / "constant" / "bottomAir" / "polyMesh",
        0.0,
        1.0,
        "bottomAir_to_heater",
        True,
    )
    _write_single_cell_region_mesh(
        tmp_path / "case" / "constant" / "heater" / "polyMesh",
        1.0,
        2.0,
        "heater_to_bottomAir",
        False,
    )
    _write_uniform_scalar_field(tmp_path / "case" / "2" / "bottomAir" / "T", 320.0)
    _write_uniform_scalar_field(tmp_path / "case" / "2" / "heater" / "T", 300.0)

    heat_flux = write_patch_heat_flux_proxy_summary(config, tmp_path, {"time": "2"})

    assert Path(heat_flux["csv"]).exists()
    assert heat_flux["available"] is True
    row = heat_flux["interfaces"][0]
    assert row["paired_face_count"] == 1
    assert row["paired_area_m2"] == 1.0
    assert row["owner_to_neighbour_flux_proxy_W_m2"] > 0.0
    assert row["owner_to_neighbour_heat_rate_proxy_W"] > 0.0
