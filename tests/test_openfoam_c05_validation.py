from __future__ import annotations

from pathlib import Path

import yaml

from science_capability_registry.openfoam.transient_cylinder_vortex_shedding.validation import validate_manifest


def _baseline_config() -> dict:
    return yaml.safe_load(
        Path("configs/openfoam/transient_cylinder_vortex_shedding/baseline_cylinder2d.yaml").read_text(
            encoding="utf-8"
        )
    )


def test_openfoam_c05_validation_rejects_missing_generated_file() -> None:
    config = _baseline_config()
    manifest = {
        "source_config": "baseline_cylinder2d.yaml",
        "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
        "backend": {"type": "dry_run_only"},
        "solver": {"name": "pimpleFoam"},
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "fields": config["fields"],
        "numerics": config["numerics"],
        "function_objects": config["function_objects"],
        "expected_outputs": [],
        "validation_targets": {},
        "generated_files": ["case/0/U"],
    }

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "generated_file.listed.case/0/p" in failed


def test_openfoam_c05_validation_rejects_disabled_force_coefficients() -> None:
    config = _baseline_config()
    manifest = {
        section: config[section]
        for section in ["backend", "solver", "template", "geometry", "mesh", "material", "fields", "numerics", "function_objects"]
    }
    manifest.update(
        {
            "source_config": "baseline_cylinder2d.yaml",
            "schema_id": "schemas/openfoam_C05_transient_cylinder_vortex_shedding.schema.json",
            "expected_outputs": config["outputs"]["expected_outputs"],
            "validation_targets": config["validation"],
            "generated_files": list(config["validation"]["required_generated_files"]),
        }
    )
    manifest["function_objects"] = {"force_coefficients": {**config["function_objects"]["force_coefficients"], "enabled": False}}

    result = validate_manifest(manifest, config)

    assert result["passed"] is False
    failed = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "function_object.force_coefficients_enabled" in failed
