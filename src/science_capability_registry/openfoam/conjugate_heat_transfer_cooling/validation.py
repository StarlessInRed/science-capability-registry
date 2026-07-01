"""Dry-run validation for OpenFOAM C07 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _interface_names(config: dict[str, Any]) -> set[str]:
    return {str(item["name"]) for item in config["interfaces"]}


def _regions(config: dict[str, Any]) -> list[str]:
    return [*config["regions"]["fluid"], *config["regions"]["solid"]]


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, section)

    backend = manifest.get("backend", {})
    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(
        checks,
        "runtime_profile.cht_multi_region",
        manifest.get("runtime_profile") in {"openfoam_com_v2112_cht", "openfoam_com_v2412_cht"},
        str(manifest.get("runtime_profile")),
    )
    _check(
        checks,
        "solver.chtMultiRegionSimpleFoam",
        manifest.get("solver", {}).get("name") == "chtMultiRegionSimpleFoam",
        "C07 uses chtMultiRegionSimpleFoam",
    )
    _check(
        checks,
        f"template.{config['template']['source_profile_key']}",
        config["template"]["source_profile_key"] in {"c07_cpu_cabinet", "c07_multi_region_heater_radiation"},
        config["template"]["source_path"],
    )
    _check(
        checks, "regions.fluid_declared", len(config["regions"]["fluid"]) >= 1, str(config["regions"]["fluid"])
    )
    _check(
        checks, "regions.solid_declared", len(config["regions"]["solid"]) >= 1, str(config["regions"]["solid"])
    )
    _check(
        checks,
        "parallel.subdomains",
        int(config["parallel"]["number_of_subdomains"]) >= 1,
        str(config["parallel"]["number_of_subdomains"]),
    )
    for region in _regions(config):
        _check(checks, f"parallel.region_subdomains.{region}", region in config["parallel"]["region_subdomains"], region)
        _check(checks, f"fields.required_by_region.{region}", region in config["fields"]["required_by_region"], region)
        _check(checks, f"materials.{region}", region in config["materials"], region)
    for name, heat_source in config["heat_sources"].items():
        if heat_source["source_type"] == "scalarSemiImplicitSource":
            passed = float(heat_source["power_W"]) > 0.0
            details = str(heat_source["power_W"])
        else:
            passed = float(heat_source["temperature_K"]) > 0.0 and bool(heat_source["boundary_patch"])
            details = f"{heat_source['boundary_patch']}={heat_source['temperature_K']}"
        _check(checks, f"physics.heat_source.{name}", passed, details)
    _check(
        checks,
        "physics.positive_initial_temperature",
        float(config["fields"]["initial_temperature_K"]) > 0.0,
        str(config["fields"]["initial_temperature_K"]),
    )

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_generated_files"]:
        _check(checks, f"generated_file.listed.{rel_path}", rel_path in generated_files, rel_path)
    for rel_path in config["mesh_workflow"]["required_generated_files"]:
        _check(checks, f"mesh_resource.listed.{rel_path}", rel_path in generated_files, rel_path)

    manifest_mesh_commands = set(manifest.get("mesh_commands", []))
    for command in config["mesh_workflow"]["command_sequence"]:
        _check(checks, f"mesh_command.planned.{command}", command in manifest_mesh_commands, command)

    manifest_radiation_commands = set(manifest.get("radiation_commands", []))
    for command in config["radiation"]["preprocessing_commands"]:
        _check(checks, f"radiation_command.planned.{command}", command in manifest_radiation_commands, command)

    manifest_interfaces = set(manifest.get("interfaces", []))
    for pair in config["validation"]["required_interface_pairs"]:
        _check(checks, f"interface_pair.planned.{pair}", pair in manifest_interfaces, pair)
    _check(checks, "interface_pairs.configured", _interface_names(config) == set(config["validation"]["required_interface_pairs"]), "configured interfaces match validation targets")

    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_generated_files"]:
            path = root / rel_path
            _check(checks, f"generated_file.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))
        region_properties = root / "case/constant/regionProperties"
        if region_properties.exists():
            text = region_properties.read_text(encoding="utf-8")
            for region in _regions(config):
                _check(checks, f"regionProperties.{region}", region in text, str(region_properties))
        else:
            _check(checks, "regionProperties.exists", False, str(region_properties))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run manifest and generated official-template multi-region CHT case files only",
        "checks": checks,
    }
