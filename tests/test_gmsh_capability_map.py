from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(".")
MAP_PATH = ROOT / "software" / "gmsh" / "capability_map.md"
INDEX_PATH = ROOT / "software" / "gmsh" / "examples_index.md"
EVIDENCE_INDEX_PATH = ROOT / "reports" / "evidence_index.yaml"

GMSH_ASSETS = {
    "C01": "software/gmsh/assets/C01_parametric_geometry_mesh_generation.yaml",
    "C02": "software/gmsh/assets/C02_boundary_physical_group_contract.yaml",
    "C03": "software/gmsh/assets/C03_mesh_refinement_quality_trend.yaml",
    "C04": "software/gmsh/assets/C04_cad_import_geometry_healing.yaml",
    "C05": "software/gmsh/assets/C05_boundary_layer_size_field_meshing.yaml",
    "C06": "software/gmsh/assets/C06_multi_solver_mesh_export_contract.yaml",
}

GMSH_TASKS = {
    "C02": "tasks/gmsh_C02_boundary_physical_group_contract_intern_task.md",
    "C03": "tasks/gmsh_C03_mesh_refinement_quality_trend_intern_task.md",
    "C04": "tasks/gmsh_C04_cad_import_geometry_healing_intern_task.md",
    "C05": "tasks/gmsh_C05_boundary_layer_size_field_meshing_intern_task.md",
    "C06": "tasks/gmsh_C06_multi_solver_mesh_export_contract_intern_task.md",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_gmsh_c01_c06_capability_map_links_assets_and_tasks() -> None:
    map_text = MAP_PATH.read_text(encoding="utf-8")
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    for c_id, asset_path in GMSH_ASSETS.items():
        asset = _read_yaml(ROOT / asset_path)
        assert asset["software"] == "Gmsh"
        assert asset["domain"] == "meshing"
        assert asset_path in index_text
        assert c_id in map_text

        if c_id == "C01":
            assert asset["benchmark_status"] == "package_skeleton_created"
        else:
            assert asset["benchmark_status"] == "benchmark_candidate"
            assert "planned_input_schema" in asset["integration_targets"]
            assert "planned_package_entrypoint" in asset["integration_targets"]

    for task_path in GMSH_TASKS.values():
        task_text = (ROOT / task_path).read_text(encoding="utf-8")
        assert "## 验证标准" in task_text
        assert task_path in _read_evidence_supporting_paths()


def test_gmsh_capability_map_evidence_entry_resolves() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {entry["evidence_id"]: entry for entry in evidence_index["evidence"]}

    evidence = evidence_by_id["gmsh_C01_C06_capability_map_2026-07-01"]
    assert evidence["asset_path"] == MAP_PATH.as_posix()
    assert evidence["status"] == "indexed"
    assert Path(evidence["primary_evidence_path"]).exists()
    for path in evidence["supporting_paths"]:
        assert Path(path).exists(), path


def _read_evidence_supporting_paths() -> set[str]:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    for entry in evidence_index["evidence"]:
        if entry["evidence_id"] == "gmsh_C01_C06_capability_map_2026-07-01":
            return set(entry["supporting_paths"])
    raise AssertionError("missing gmsh_C01_C06_capability_map_2026-07-01")
