from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from science_capability_registry.gmsh.parametric_geometry_mesh_generation.runner import run


def test_gmsh_c01_python_api_runtime_smoke(tmp_path: Path) -> None:
    try:
        import gmsh  # noqa: F401
    except ModuleNotFoundError:
        pytest.skip("gmsh Python API is not installed in this environment")

    config = yaml.safe_load(Path("configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml").read_text(encoding="utf-8"))
    config["backend"]["type"] = "python_api"
    result = run(config=config, output_dir=tmp_path, dry_run=False)

    assert result["validation"]["passed"] is True
    assert (tmp_path / "case.msh").exists()
    assert result["runtime"]["node_count"] >= config["validation"]["min_node_count"]
    assert "fluid_domain" in result["runtime"]["physical_groups"]
