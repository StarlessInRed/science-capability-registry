from __future__ import annotations

import io
import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.workbench_parameter_integration.config import validate_case_config
from science_capability_registry.fluent.workbench_parameter_integration.runner import run


def _minimal_wbpj() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<Storage>
  <Project Version="9.1">
    <framework-build-version valType="String">20.2.210.0</framework-build-version>
    <external-version-string valType="String">2020 R2</external-version-string>
    <last-saved-utc valType="String">05/11/2020 18:58:06</last-saved-utc>
  </Project>
  <Object Name="/Parameters/Parameter:P1" Version="1.0">
    <class-type valType="String">Parameter</class-type>
    <object-name valType="String">P1</object-name>
    <member-data valType="String">{"DisplayText": "hcpos", "Expression": "90", "Usage": "Input", "Value": {"value": "90"}, "ValueSpec": {"QuantityName": "Dimensionless"}}</member-data>
  </Object>
  <Object Name="/Parameters/Parameter:P2" Version="1.0">
    <class-type valType="String">Parameter</class-type>
    <object-name valType="String">P2</object-name>
    <member-data valType="String">{"DisplayText": "ftpos", "Expression": "25", "Usage": "Input", "Value": {"value": "25"}, "ValueSpec": {"QuantityName": "Dimensionless"}}</member-data>
  </Object>
  <Object Name="/Parameters/Parameter:P3" Version="1.0">
    <class-type valType="String">Parameter</class-type>
    <object-name valType="String">P3</object-name>
    <member-data valType="String">{"DisplayText": "wsfpos", "Expression": "175", "Usage": "Input", "Value": {"value": "175"}, "ValueSpec": {"QuantityName": "Dimensionless"}}</member-data>
  </Object>
</Storage>
"""


def _write_fixture_zip(root: Path) -> None:
    package_dir = root / "Fluent_Workbench_Tutorial_Package"
    package_dir.mkdir(parents=True)
    nested_bytes = io.BytesIO()
    with zipfile.ZipFile(nested_bytes, "w") as nested:
        nested.writestr("fluent-workbench-param.wbpj", _minimal_wbpj())
        nested.writestr("fluent-workbench-param_files/dp0/designPoint.wbdp", "<Storage />")
        nested.writestr("fluent-workbench-param_files/session_files/journal1.wbjn", "journal")
        nested.writestr("fluent-workbench-param_files/user_files/DesignPointLog.csv", "# comment\nName, P1, P2, P3\nDP 0, 90, 25, 175\n")
        nested.writestr("fluent-workbench-param_files/dp0/FFF/DM/FFF.agdb", "geometry")
        nested.writestr("fluent-workbench-param_files/dp0/global/MECH/FFF.mshdb", "meshdb")
    with zipfile.ZipFile(package_dir / "workbench_parameter.zip", "w") as outer:
        outer.writestr("workbench_parameter/fluent-workbench-param.wbpz", nested_bytes.getvalue())


def _fixture_config() -> dict:
    config = yaml.safe_load(
        Path("configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(deepcopy(config))


def test_fluent_c08_runner_writes_workbench_manifest(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    result = run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["current_parameter_count"] == 3
    assert result["metrics"]["workbench_project_version"] == "2020 R2"
    assert result["metrics"]["workbench_runtime_status"] == "not_executed_in_static_preflight"
    assert (tmp_path / "out" / "parameter_table.csv").exists()


def test_fluent_c08_runner_rejects_non_dry_run(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "sources"
    _write_fixture_zip(source_root)
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    try:
        run(config=_fixture_config(), output_dir=tmp_path / "out", dry_run=False)
    except ValueError as exc:
        assert "dry_run" in str(exc)
    else:
        raise AssertionError("expected C08 non-dry-run rejection")
