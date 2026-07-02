"""Validation helpers for Fluent C07 heat-transfer source readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    entries = manifest["entries"]
    archive = manifest["archive"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "archive_status": archive["archive_status"],
        "archive_entry_count": archive["entry_count"],
        "case_entry_count": archive["entry_kind_counts"].get("case", 0),
        "data_entry_count": archive["entry_kind_counts"].get("data", 0),
        "case_data_pair_count": len(manifest["case_data_pairs"]),
        "total_uncompressed_bytes": sum(int(entry["size"]) for entry in entries),
        "heat_rate_runtime_status": "not_extracted_in_source_manifest",
        "temperature_runtime_status": "not_extracted_in_source_manifest",
    }
    if "runtime_metrics" in manifest:
        runtime_metrics = manifest["runtime_metrics"]
        result.update(runtime_metrics)
        result["heat_rate_runtime_status"] = runtime_metrics.get(
            "heat_rate_runtime_status",
            "case_data_read_only_no_heat_rate_extraction",
        )
        result["temperature_runtime_status"] = runtime_metrics.get(
            "temperature_runtime_status",
            "case_data_read_only_no_temperature_report",
        )
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    archive = manifest["archive"]

    _check(checks, "archive.readable", archive["archive_status"] == "readable", archive["error_message"])
    for required_kind in config["validation"]["required_entry_classes"]:
        _check(
            checks,
            f"archive.entry_class.{required_kind}",
            archive["entry_kind_counts"].get(required_kind, 0) > 0,
            json.dumps(archive["entry_kind_counts"], sort_keys=True),
        )
    _check(
        checks,
        "source.case_data_pair_count",
        len(manifest["case_data_pairs"]) >= config["validation"]["min_case_data_pairs"],
        str(len(manifest["case_data_pairs"])),
    )
    if config["backend"]["type"] == "fluent_case_data_read_smoke":
        runtime_metrics = manifest.get("runtime_metrics", {})
        _check(checks, "runtime.return_code_zero", runtime_metrics.get("fluent_return_code") == 0, str(runtime_metrics.get("fluent_return_code")))
        _check(checks, "runtime.mesh_check_completed", bool(runtime_metrics.get("mesh_check_completed")), str(runtime_metrics.get("mesh_check_completed")))
        _check(checks, "runtime.no_fluent_errors", runtime_metrics.get("fluent_error_count") == 0, str(runtime_metrics.get("fluent_error_count")))
        _check(
            checks,
            "runtime.warning_budget",
            runtime_metrics.get("fluent_warning_count", 999999) <= config["runtime_smoke"]["max_warning_count"],
            f"{runtime_metrics.get('fluent_warning_count')} <= {config['runtime_smoke']['max_warning_count']}",
        )
        _check(
            checks,
            "runtime.case_cell_count_optional",
            runtime_metrics.get("mesh_cell_count") is None or runtime_metrics["mesh_cell_count"] > 0,
            str(runtime_metrics.get("mesh_cell_count")),
        )
        reports = config["runtime_smoke"].get("thermal_reports")
        if reports is not None:
            temperature_min = runtime_metrics.get("temperature_min_k")
            temperature_max = runtime_metrics.get("temperature_max_k")
            surface_temperatures = runtime_metrics.get("surface_area_weighted_temperature_k", {})
            _check(
                checks,
                "runtime.temperature_min_present",
                isinstance(temperature_min, (int, float)),
                str(temperature_min),
            )
            _check(
                checks,
                "runtime.temperature_max_present",
                isinstance(temperature_max, (int, float)),
                str(temperature_max),
            )
            _check(
                checks,
                "runtime.temperature_range_ordered",
                isinstance(temperature_min, (int, float))
                and isinstance(temperature_max, (int, float))
                and temperature_min <= temperature_max,
                f"min={temperature_min}, max={temperature_max}",
            )
            for surface in reports["temperature_surfaces"]:
                _check(
                    checks,
                    f"runtime.surface_temperature.{surface}",
                    isinstance(surface_temperatures.get(surface), (int, float)),
                    str(surface_temperatures.get(surface)),
                )
            heat_rates = runtime_metrics.get("heat_transfer_rates_w", {})
            heat_balance_error = runtime_metrics.get("heat_transfer_balance_relative_error")
            _check(
                checks,
                "runtime.heat_transfer_rates_present",
                reports["heat_transfer_flux_all_boundaries"] is False or (isinstance(heat_rates, dict) and "Net" in heat_rates and len(heat_rates) > 1),
                json.dumps(heat_rates, sort_keys=True),
            )
            _check(
                checks,
                "runtime.heat_transfer_balance_error",
                reports["heat_transfer_flux_all_boundaries"] is False
                or (
                    isinstance(heat_balance_error, (int, float))
                    and heat_balance_error <= reports["max_energy_balance_relative_error"]
                ),
                f"{heat_balance_error} <= {reports['max_energy_balance_relative_error']}",
            )

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            if rel_path == "stderr.txt":
                passed = path.exists()
            else:
                passed = path.exists() and path.stat().st_size > 0
            _check(checks, f"artifact.exists.{rel_path}", passed, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C07 heat-transfer case/data source manifest/read smoke; thermal reports are bounded to this case/data pair and do not claim CHT interface validation",
        "checks": checks,
        "details": {
            "case_data_pairs": manifest["case_data_pairs"],
            "no_claims": config["validation"]["no_claims"],
        },
    }
