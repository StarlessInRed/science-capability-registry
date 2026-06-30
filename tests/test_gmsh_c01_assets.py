from __future__ import annotations

from pathlib import Path

import yaml


ASSET_PATH = Path("software/gmsh/assets/C01_parametric_geometry_mesh_generation.yaml")
INDEX_PATH = Path("software/gmsh/examples_index.md")
TASK_PATH = Path("tasks/gmsh_C01_parametric_geometry_mesh_generation_intern_task.md")


def test_gmsh_c01_asset_index_and_task_are_linked() -> None:
    asset = yaml.safe_load(ASSET_PATH.read_text(encoding="utf-8"))
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    task_text = TASK_PATH.read_text(encoding="utf-8")

    assert asset["asset_id"] == "C01_parametric_geometry_mesh_generation"
    assert asset["card_status"] == "review"
    assert asset["benchmark_status"] == "package_skeleton_created"
    assert ASSET_PATH.as_posix() in index_text
    assert "schemas/gmsh_C01_parametric_geometry_mesh_generation.schema.json" in task_text
