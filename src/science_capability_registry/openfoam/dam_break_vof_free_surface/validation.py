"""Dry-run validation for OpenFOAM C06 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, section)
    backend = manifest.get("backend", {})
    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(checks, "solver.interFoam", manifest.get("solver", {}).get("name") == "interFoam", "C06 uses interFoam")
    _check(checks, "template.official_damBreak", "damBreak" in config["template"]["source_path"], config["template"]["source_path"])
    _check(checks, "physics.positive_gravity", float(config["physics"]["gravity_m_s2"]) > 0.0, str(config["physics"]["gravity_m_s2"]))
    _check(checks, "initial_water.height_positive", float(config["initial_conditions"]["water_column_height_m"]) > 0.0, str(config["initial_conditions"]["water_column_height_m"]))
    sampling = config["validation"]["sampling_parity"]
    full_horizon = config["validation"]["full_horizon"]
    reference = config["validation"]["reference_policy"]
    if config["validation"]["gate"] == "double-v":
        _check(checks, "double_v.sampling_parity", sampling["status"] == "passed" and sampling["source"] != "python_alpha_postprocess_only" and sampling["native_sampling_enabled"] is True, str(sampling))
        _check(checks, "double_v.full_horizon", full_horizon["status"] == "passed", str(full_horizon))
        _check(checks, "double_v.reference_policy", reference["status"] == "passed" and reference["source_type"] in {"external_benchmark", "independent_reference"}, str(reference))
    else:
        _check(checks, "double_v.not_claimed", reference["status"] != "passed" or config["validation"]["gate"] != "double-v", str(reference))
    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_generated_files"]:
        _check(checks, f"generated_file.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(checks, f"generated_file.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
    return {"passed": all(item["passed"] for item in checks), "gate": config["validation"]["gate"], "scope": "dry-run manifest and generated official-template case files only", "checks": checks}
