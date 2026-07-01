"""Validation for OpenFOAM C08 dry-run and runtime artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

PROMOTION_GATES = {"targeted-regression", "integration", "double-v", "full-regression"}


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _relative_error(value: Any, reference: Any) -> float | None:
    if reference in (None, 0):
        return None
    if not _is_finite(value) or not _is_finite(reference):
        return None
    return abs(float(value) - float(reference)) / abs(float(reference))


def validate_manifest(
    manifest: dict[str, Any],
    config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    backend = manifest.get("backend", {})
    solver = manifest.get("solver", {})
    generated_files = set(manifest.get("generated_files", []))
    fields = config["fields"]

    _check(checks, "backend.dry_run_only", backend.get("type") == "dry_run_only", f"backend={backend.get('type')!r}")
    _check(checks, "solver.rhoCentralFoam", solver.get("name") == "rhoCentralFoam", json.dumps(solver, ensure_ascii=False))
    _check(checks, "template.official_forwardStep", "rhoCentralFoam/forwardStep" in config["template"]["source_path"], config["template"]["source_path"])
    _check(checks, "thermo.hePsiThermo", config["thermophysical_properties"]["thermo_model"] == "hePsiThermo", json.dumps(config["thermophysical_properties"], ensure_ascii=False))
    _check(checks, "field.rho.derived", fields["rho"]["source"] == "derived_from_thermophysical_state", json.dumps(fields["rho"], ensure_ascii=False))
    _check(checks, "field.U.present", "U" in fields and fields["U"]["dimensions"] == "[0 1 -1 0 0 0 0]", json.dumps(fields.get("U", {}), ensure_ascii=False))
    _check(checks, "field.p.present", "p" in fields and fields["p"]["dimensions"] == "[1 -1 -2 0 0 0 0]", json.dumps(fields.get("p", {}), ensure_ascii=False))
    _check(checks, "field.T.present", "T" in fields and fields["T"]["dimensions"] == "[0 0 0 1 0 0 0]", json.dumps(fields.get("T", {}), ensure_ascii=False))
    shock_search_window = config["postprocess"]["shock_search_window_m"]
    _check(checks, "postprocess.sample_lines", bool(config["postprocess"]["sample_lines"]), json.dumps(config["postprocess"], ensure_ascii=False))
    _check(checks, "postprocess.shock_search_window_ordered", shock_search_window[0] < shock_search_window[1], json.dumps(config["postprocess"], ensure_ascii=False))
    _check(checks, "postprocess.windows_ordered", config["postprocess"]["upstream_window_m"][1] < config["postprocess"]["downstream_window_m"][0], json.dumps(config["postprocess"], ensure_ascii=False))
    _check(checks, "numerics.max_courant_matches_validation", float(config["numerics"]["control"]["max_courant"]) <= float(config["validation"]["max_courant"]), json.dumps(config["numerics"]["control"], ensure_ascii=False))

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
        "scope": "dry-run manifest and generated rhoCentralFoam forwardStep template case files only",
        "checks": checks,
    }


def validate_runtime_metrics(metrics: dict[str, Any], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    runtime_commands = metrics.get("runtime", {}).get("commands", [])
    solver = metrics.get("solver", {})
    postprocess = metrics.get("postprocess", {})
    field_extrema = postprocess.get("field_extrema", {})
    shock = postprocess.get("shock", {})
    conservation = postprocess.get("conservation", {})
    reference = config["shock_reference"]

    for command in config["solver"]["command_sequence"]:
        match = next((item for item in runtime_commands if item.get("command") == command), None)
        _check(checks, f"command.{command}.returncode", bool(match and match.get("returncode") == 0), json.dumps(match or {}, ensure_ascii=False))

    _check(checks, "solver.started", solver.get("started") is True, "rhoCentralFoam log signal found")
    _check(checks, "solver.no_fatal_error", solver.get("fatal_error_detected") is False, "FOAM FATAL and true FPE must be absent")
    _check(checks, "solver.max_courant", _is_finite(solver.get("max_courant")) and float(solver["max_courant"]) <= float(config["validation"]["max_courant"]), f"value={solver.get('max_courant')}")
    _check(checks, "solver.final_time", _is_finite(solver.get("final_time_s")) and float(solver["final_time_s"]) >= float(config["validation"]["minimum_final_time_s"]), f"value={solver.get('final_time_s')}")

    for field_name, min_key in [("p", "min_pressure"), ("T", "min_temperature"), ("rho", "min_density")]:
        field = field_extrema.get(field_name, {})
        passed = field.get("available") is True and field.get("finite") is True and _is_finite(field.get("min")) and float(field["min"]) >= float(config["validation"][min_key])
        _check(checks, f"field.{field_name}.positive_finite", passed, json.dumps(field, ensure_ascii=False))
    u_field = field_extrema.get("U", {})
    _check(checks, "field.U.finite", u_field.get("available") is True and u_field.get("finite") is True, json.dumps(u_field, ensure_ascii=False))

    _check(checks, "postprocess.shock.available", shock.get("available") is True, json.dumps(shock, ensure_ascii=False))
    _check(
        checks,
        "postprocess.pressure_jump_ratio_sanity",
        _is_finite(shock.get("pressure_jump_ratio")) and float(shock["pressure_jump_ratio"]) > 1.0,
        f"value={shock.get('pressure_jump_ratio')}",
    )
    _check(
        checks,
        "postprocess.density_jump_ratio_sanity",
        _is_finite(shock.get("density_jump_ratio")) and float(shock["density_jump_ratio"]) > 1.0,
        f"value={shock.get('density_jump_ratio')}",
    )
    shock_ref = reference.get("shock_position_reference_m")
    if shock_ref is not None:
        shock_error = abs(float(shock.get("shock_position_m", math.nan)) - float(shock_ref)) if _is_finite(shock.get("shock_position_m")) else math.inf
        _check(checks, "postprocess.shock_position_reference", shock_error <= float(config["validation"]["max_shock_position_abs_error_m"]), f"value={shock.get('shock_position_m')}, reference={shock_ref}")
    else:
        _check(checks, "postprocess.shock_reference_declared_missing", reference["reference_policy"] == "configured_reference_required_for_promotion", json.dumps(reference, ensure_ascii=False))

    pressure_ref = reference.get("pressure_jump_ratio_reference")
    density_ref = reference.get("density_jump_ratio_reference")
    for metric_name, metric_ref in [("pressure_jump_ratio", pressure_ref), ("density_jump_ratio", density_ref)]:
        rel_error = _relative_error(shock.get(metric_name), metric_ref)
        if metric_ref is None:
            _check(checks, f"postprocess.{metric_name}.reference_missing", reference["reference_policy"] == "configured_reference_required_for_promotion", json.dumps(reference, ensure_ascii=False))
        else:
            _check(checks, f"postprocess.{metric_name}.reference", rel_error is not None and rel_error <= float(config["validation"]["max_jump_ratio_rel_error"]), f"value={shock.get(metric_name)}, reference={metric_ref}")

    if config["validation"]["gate"] in PROMOTION_GATES:
        reference_targets_present = all(
            _is_finite(reference.get(key))
            for key in [
                "shock_position_reference_m",
                "pressure_jump_ratio_reference",
                "density_jump_ratio_reference",
            ]
        )
        _check(
            checks,
            "postprocess.shock_reference_required_for_promotion",
            reference_targets_present,
            json.dumps(reference, ensure_ascii=False),
        )

    _check(
        checks,
        "boundary_flux.mass_imbalance_proxy",
        conservation.get("available") is True
        and conservation.get("method") == "boundary_flux_owner_cell_proxy"
        and _is_finite(conservation.get("boundary_flux_mass_imbalance_proxy"))
        and abs(float(conservation["boundary_flux_mass_imbalance_proxy"])) <= float(config["validation"]["max_boundary_flux_mass_imbalance_proxy"]),
        json.dumps(conservation, ensure_ascii=False),
    )
    if config["validation"]["gate"] in PROMOTION_GATES:
        native_or_face_flux = conservation.get("method") in {"native_openfoam_face_flux", "face_field_integration"}
        _check(
            checks,
            "boundary_flux.native_or_face_flux_parity_required_for_promotion",
            native_or_face_flux,
            json.dumps(conservation, ensure_ascii=False),
        )
    _check(
        checks,
        "boundary_flux.total_energy_imbalance_proxy",
        conservation.get("available") is True
        and conservation.get("method") == "boundary_flux_owner_cell_proxy"
        and _is_finite(conservation.get("boundary_flux_total_energy_imbalance_proxy"))
        and abs(float(conservation["boundary_flux_total_energy_imbalance_proxy"])) <= float(config["validation"]["max_boundary_flux_total_energy_imbalance_proxy"]),
        json.dumps(conservation, ensure_ascii=False),
    )

    for rel_path in config["outputs"].get("expected_outputs", []):
        if rel_path in {"manifest.json", "validation.json", "validation_report.md"}:
            continue
        path = output_dir / rel_path
        _check(checks, f"artifact.expected.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": "local OpenFOAM C08 runtime, field sanity, shock metrics, and boundary-flux proxy",
        "checks": checks,
    }
