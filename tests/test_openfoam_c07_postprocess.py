from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.conjugate_heat_transfer_cooling.postprocess import (
    write_interface_balance_summary,
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
