"""Dry-run validation for OpenFOAM C01 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def validate_manifest(
    manifest: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a dry-run manifest without claiming solver success."""
    checks: list[dict[str, Any]] = []
    required_sections = config["validation"]["required_manifest_sections"]
    for section in required_sections:
        _check(
            checks,
            f"manifest.section.{section}",
            section in manifest,
            f"required section {section}",
        )

    backend = manifest.get("backend", {})
    _check(
        checks,
        "backend.dry_run_only",
        backend.get("type") == "dry_run_only",
        f"backend type is {backend.get('type')!r}",
    )

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_generated_files"]:
        _check(
            checks,
            f"generated_file.listed.{rel_path}",
            rel_path in generated_files,
            rel_path,
        )

    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(
                checks,
                f"generated_file.exists.{rel_path}",
                path.exists() and path.stat().st_size > 0,
                str(path),
            )

    mesh = config["mesh"]
    fields = config["fields"]
    _check(
        checks,
        "mesh.two_dimensional_empty_patch",
        mesh["patches"]["frontAndBack"]["type"] == "empty"
        and fields["U"]["boundaries"]["frontAndBack"]["type"] == "empty"
        and fields["p"]["boundaries"]["frontAndBack"]["type"] == "empty",
        "frontAndBack patch and field boundaries must be empty",
    )
    _check(
        checks,
        "physics.reynolds_number",
        float(config["material"]["reynolds_number"]) > 0.0,
        f"Re={config['material']['reynolds_number']}",
    )

    return {
        "passed": all(check["passed"] for check in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run manifest and generated case files only",
        "checks": checks,
    }
