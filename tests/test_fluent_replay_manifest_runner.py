from __future__ import annotations

import json
import zipfile
from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.official_replay_manifest.runner import run


def _write_zip(path: Path, names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, "fixture")


def test_fluent_replay_manifest_runner_classifies_sources(monkeypatch, tmp_path: Path) -> None:
    source_root = tmp_path / "sources"
    (source_root / "legacy" / "elbow").mkdir(parents=True)
    (source_root / "legacy" / "elbow" / "elbow.cas").write_text("case", encoding="utf-8")
    (source_root / "legacy" / "elbow" / "elbow.dat").write_text("data", encoding="utf-8")
    (source_root / "manual.pdf").write_text("pdf", encoding="utf-8")
    _write_zip(source_root / "case_data.zip", ["case/foo.cas.h5", "case/foo.dat.h5"])
    _write_zip(source_root / "mesh.zip", ["mesh/axial_comp.msh.h5"])
    _write_zip(source_root / "aero.zip", ["aero/wing.cas.h5", "aero/reference_data/ref-wing.csv"])
    _write_zip(source_root / "wb.zip", ["project/fluent-workbench-param.wbpz"])
    monkeypatch.setenv("FLUENT_TUTORIAL_ROOT", str(source_root))

    base_config = yaml.safe_load(Path("configs/fluent/official_replay_manifest/c01_c08_sources.yaml").read_text(encoding="utf-8"))
    config = deepcopy(base_config)
    config["source_packages"] = [
        {
            "source_id": "C01_legacy",
            "seed_id": "C01",
            "source_kind": "legacy_directory",
            "source_role": "legacy",
            "rel_path": "legacy/elbow",
            "expected_entry_classes": ["case", "data"],
        },
        {
            "source_id": "C02_pdf",
            "seed_id": "C02",
            "source_kind": "reference_file",
            "source_role": "manual",
            "rel_path": "manual.pdf",
            "expected_entry_classes": ["reference_document"],
        },
        {
            "source_id": "C03_case",
            "seed_id": "C03",
            "source_kind": "zip_archive",
            "source_role": "case",
            "rel_path": "case_data.zip",
            "expected_entry_classes": ["case", "data"],
        },
        {
            "source_id": "C04_aero",
            "seed_id": "C04",
            "source_kind": "zip_archive",
            "source_role": "aero",
            "rel_path": "aero.zip",
            "expected_entry_classes": ["case", "reference_csv"],
        },
        {
            "source_id": "C05_mesh",
            "seed_id": "C05",
            "source_kind": "zip_archive",
            "source_role": "mesh",
            "rel_path": "mesh.zip",
            "expected_entry_classes": ["mesh"],
        },
        {
            "source_id": "C06_mesh",
            "seed_id": "C06",
            "source_kind": "zip_archive",
            "source_role": "mesh",
            "rel_path": "mesh.zip",
            "expected_entry_classes": ["mesh"],
        },
        {
            "source_id": "C07_case",
            "seed_id": "C07",
            "source_kind": "zip_archive",
            "source_role": "case_data",
            "rel_path": "case_data.zip",
            "expected_entry_classes": ["case", "data"],
        },
        {
            "source_id": "C08_wb",
            "seed_id": "C08",
            "source_kind": "zip_archive",
            "source_role": "workbench",
            "rel_path": "wb.zip",
            "expected_entry_classes": ["workbench_archive"],
        },
    ]
    for binding in config["capability_bindings"]:
        binding["source_ids"] = [source["source_id"] for source in config["source_packages"] if source["seed_id"] == binding["seed_id"]]

    result = run(config=config, output_dir=tmp_path / "out", dry_run=True)

    assert result["validation"]["passed"] is True
    assert result["metrics"]["entry_kind_totals"]["workbench_archive"] == 1
    assert result["metrics"]["entry_kind_totals"]["reference_csv"] == 1
    assert (tmp_path / "out" / "official_replay_manifest.json").exists()
    manifest = json.loads((tmp_path / "out" / "official_replay_manifest.json").read_text(encoding="utf-8"))
    assert any(package["summary"]["entrypoint_class"] == "workbench_project" for package in manifest["packages"])
