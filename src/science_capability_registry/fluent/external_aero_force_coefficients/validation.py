"""Validation helpers for Fluent C04 external-aero reference parsing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def summarize_metrics(manifest: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    reference_tables = manifest["reference_tables"]
    row_counts = {table["reference_id"]: table["row_count"] for table in reference_tables}
    cl_table = next((table for table in reference_tables if table["reference_role"] == "lift_curve"), None)
    cp_tables = [table for table in reference_tables if table["reference_role"] == "pressure_coefficient_section"]
    result = {
        "capability_id": manifest["capability_id"],
        "case_id": manifest["case_id"],
        "archive_status": manifest["archive"]["archive_status"],
        "archive_entry_count": manifest["archive"]["entry_count"],
        "reference_table_count": len(reference_tables),
        "reference_row_counts": row_counts,
        "case_entry_count": manifest["archive"]["entry_kind_counts"].get("case", 0),
        "mesh_entry_count": manifest["archive"]["entry_kind_counts"].get("mesh", 0),
        "reference_csv_count": manifest["archive"]["entry_kind_counts"].get("reference_csv", 0),
        "design_csv_count": manifest["archive"]["entry_kind_counts"].get("design_or_table_csv", 0),
        "cl_curve_monotonic_non_decreasing": bool(cl_table and cl_table["trend_checks"]["cl_monotonic_non_decreasing"]),
        "cp_section_count": len(cp_tables),
        "pressure_drop_runtime_status": "not_applicable_for_c04_reference_parser",
        "force_runtime_status": "not_extracted_in_reference_parser",
    }
    if validation is not None:
        result["validation"] = {"passed": bool(validation["passed"]), "gate": validation["gate"]}
    return result


def validate_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    archive = manifest["archive"]
    reference_tables = manifest["reference_tables"]
    tables_by_id = {table["reference_id"]: table for table in reference_tables}
    tables_by_role: dict[str, list[dict[str, Any]]] = {}
    for table in reference_tables:
        tables_by_role.setdefault(str(table["reference_role"]), []).append(table)

    _check(checks, "archive.readable", archive["archive_status"] == "readable", archive["error_message"])
    for required_kind in config["validation"]["required_entry_classes"]:
        _check(
            checks,
            f"archive.entry_class.{required_kind}",
            archive["entry_kind_counts"].get(required_kind, 0) > 0,
            json.dumps(archive["entry_kind_counts"], sort_keys=True),
        )
    for reference in config["reference_csvs"]:
        table = tables_by_id.get(reference["reference_id"])
        _check(checks, f"reference.present.{reference['reference_id']}", table is not None, reference["entry_path"])
        if table is not None:
            _check(
                checks,
                f"reference.columns.{reference['reference_id']}",
                set(reference["required_columns"]).issubset(set(table["columns"])),
                json.dumps(table["columns"], ensure_ascii=False),
            )
            _check(
                checks,
                f"reference.rows.{reference['reference_id']}",
                table["row_count"] >= reference["min_rows"],
                f"{table['row_count']} >= {reference['min_rows']}",
            )
            _check(
                checks,
                f"reference.finite.{reference['reference_id']}",
                table["finite_numeric_values"] >= len(reference["required_columns"]) * reference["min_rows"],
                json.dumps(
                    {
                        "finite_numeric_values": table["finite_numeric_values"],
                        "skipped_non_numeric_row_count": table.get("skipped_non_numeric_row_count", 0),
                    },
                    ensure_ascii=False,
                ),
            )
    for required_role in config["validation"]["required_reference_roles"]:
        _check(
            checks,
            f"reference.role.{required_role}",
            bool(tables_by_role.get(required_role)),
            json.dumps(sorted(tables_by_role), ensure_ascii=False),
        )
    for trend_check in config["validation"]["trend_checks"]:
        if trend_check == "lift_curve_cl_monotonic_non_decreasing":
            lift_tables = tables_by_role.get("lift_curve", [])
            passed = any(table["trend_checks"].get("cl_monotonic_non_decreasing") for table in lift_tables)
            _check(checks, f"trend.{trend_check}", passed, json.dumps([table["trend_checks"] for table in lift_tables]))
        else:
            _check(checks, f"trend.{trend_check}", False, f"unsupported trend check {trend_check}")
    cl_table = next((table for table in reference_tables if table["reference_role"] == "lift_curve"), None)
    _check(
        checks,
        "physics.lift_curve_trend",
        bool(cl_table and cl_table["trend_checks"]["cl_monotonic_non_decreasing"]),
        json.dumps(cl_table["trend_checks"] if cl_table else {}, ensure_ascii=False),
    )

    generated_files = set(manifest.get("generated_files", []))
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)
    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            _check(checks, f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "Fluent C04 aero reference CSV parser; no Fluent solver execution or force/Cp replay claim",
        "checks": checks,
        "details": {
            "no_claims": config["validation"]["no_claims"],
            "reference_tables": [table["reference_id"] for table in reference_tables],
        },
    }
