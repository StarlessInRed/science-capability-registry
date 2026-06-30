"""Dry-run validation for OpenFOAM C07 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _interface_names(config: dict[str, Any]) -> set[str]:
    return {str(item["name"]) for item in config["interfaces"]}


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, section)

    backend = manifest.get("backend", {})
    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(
        checks,
        "runtime_profile.openfoam_com_v2112_cht",
        manifest.get("runtime_profile") == "openfoam_com_v2112_cht",
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
        "template.official_cpuCabinet",
        "cpuCabinet" in config["template"]["source_path"],
        config["template"]["source_path"],
    )
    _check(
        checks,
        "regions.fluid_domain0",
        config["regions"]["fluid"] == ["domain0"],
        str(config["regions"]["fluid"]),
    )
    _check(
        checks,
        "regions.solid_cpu_and_fins",
        config["regions"]["solid"] == ["v_CPU", "v_fins"],
        str(config["regions"]["solid"]),
    )
    _check(
        checks,
        "parallel.subdomains",
        int(config["parallel"]["number_of_subdomains"]) == 10,
        str(config["parallel"]["number_of_subdomains"]),
    )
    _check(
        checks,
        "physics.positive_heat_source",
        float(config["heat_sources"]["v_CPU"]["power_W"]) > 0.0,
        str(config["heat_sources"]["v_CPU"]["power_W"]),
    )
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
            _check(checks, "regionProperties.domain0", "domain0" in text, str(region_properties))
            _check(checks, "regionProperties.v_CPU", "v_CPU" in text, str(region_properties))
            _check(checks, "regionProperties.v_fins", "v_fins" in text, str(region_properties))
        else:
            _check(checks, "regionProperties.exists", False, str(region_properties))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "dry-run manifest and generated official-template multi-region CHT case files only",
        "checks": checks,
    }
