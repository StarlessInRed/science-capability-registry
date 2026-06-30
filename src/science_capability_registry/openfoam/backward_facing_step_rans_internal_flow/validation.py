"""Dry-run validation for OpenFOAM C03 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")
    backend = manifest.get("backend", {})
    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(checks, "solver.simpleFoam", manifest.get("solver", {}).get("name") == "simpleFoam", "C03 uses simpleFoam")
    _check(checks, "template.official_pitzDaily", "pitzDaily" in config["template"]["source_path"], config["template"]["source_path"])
    _check(checks, "physics.positive_inlet_velocity", float(config["material"]["inlet_velocity_m_s"]) > 0.0, str(config["material"]["inlet_velocity_m_s"]))
    _check(checks, "physics.positive_reynolds", float(config["material"]["reynolds_number_H"]) > 0.0, str(config["material"]["reynolds_number_H"]))
    _check(checks, "mesh.refinement_scale", float(config["mesh"]["cell_count_scale"]) >= 1.0, str(config["mesh"]["cell_count_scale"]))
    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_generated_files"]:
        _check(checks, f"generated_file.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(checks, f"generated_file.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run manifest and generated official-template case files only",
        "checks": checks,
    }
