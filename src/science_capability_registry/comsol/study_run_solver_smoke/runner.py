"""Runner for COMSOL C05 study/solver smoke contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from science_capability_registry.comsol.heat_rectangle_livelink import (
    run_heat_rectangle_stage,
)
from science_capability_registry.comsol.static_contract import REPO_ROOT

SCHEMA_ID = "schemas/comsol_C05_study_run_solver_smoke.schema.json"
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
        "study_run_solver_smoke",
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
