"""Runner for COMSOL C04 physics/boundary assignment contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from science_capability_registry.comsol.heat_rectangle_livelink import (
    run_heat_rectangle_stage,
)
from science_capability_registry.comsol.static_contract import REPO_ROOT

SCHEMA_ID = "schemas/comsol_C04_physics_boundary_assignment_contract.schema.json"
SCHEMA_PATH = REPO_ROOT / SCHEMA_ID


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
    backend: str | None = None,
) -> dict[str, Any]:
    return run_heat_rectangle_stage(
        SCHEMA_PATH,
        SCHEMA_ID,
        "physics_boundary_assignment_contract",
        config_path=config_path,
        config=config,
        output_dir=output_dir,
        dry_run=dry_run,
        backend=backend,
    )


def run_from_config(
    config_path: str | Path, output_dir: str | Path | None = None
) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
