"""Shared MATLAB LiveLink rectangle smoke runner for COMSOL C03-C06."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any, NamedTuple

from science_capability_registry.comsol.model_construction_api_contract.validation import (
    summarize_environment_checks,
)
from science_capability_registry.comsol.static_contract import (
    load_static_config,
    repo_relative_path,
    run_static_contract,
    validate_static_config,
)


class StageSpec(NamedTuple):
    stage: str
    script_name: str
    runtime_status_passed: str
    runtime_status_failed: str
    matlab_artifacts: tuple[str, ...]
    static_runtime_artifacts: tuple[str, ...]
    solves_study: bool
    extracts_results: bool


STAGE_SPECS: dict[str, StageSpec] = {
    "geometry_mesh_import_contract": StageSpec(
        stage="geometry_mesh_import_contract",
        script_name="matlab_c03_heat_rectangle_smoke.m",
        runtime_status_passed="matlab_livelink_geometry_mesh_passed",
        runtime_status_failed="matlab_livelink_geometry_mesh_failed",
        matlab_artifacts=(
            "geometry_manifest.json",
            "mesh_manifest.json",
            "selection_map.json",
        ),
        static_runtime_artifacts=(
            "geometry_manifest.json",
            "mesh_manifest.json",
            "selection_map.json",
        ),
        solves_study=False,
        extracts_results=False,
    ),
    "physics_boundary_assignment_contract": StageSpec(
        stage="physics_boundary_assignment_contract",
        script_name="matlab_c04_heat_rectangle_smoke.m",
        runtime_status_passed="matlab_livelink_assignment_passed",
        runtime_status_failed="matlab_livelink_assignment_failed",
        matlab_artifacts=(
            "physics_assignment_manifest.json",
            "boundary_assignment_manifest.json",
            "unit_policy.json",
        ),
        static_runtime_artifacts=(
            "physics_assignment_manifest.json",
            "boundary_assignment_manifest.json",
            "unit_policy.json",
        ),
        solves_study=False,
        extracts_results=False,
    ),
    "study_run_solver_smoke": StageSpec(
        stage="study_run_solver_smoke",
        script_name="matlab_c05_heat_rectangle_smoke.m",
        runtime_status_passed="matlab_livelink_solver_smoke_passed",
        runtime_status_failed="matlab_livelink_solver_smoke_failed",
        matlab_artifacts=("solver_manifest.json", "dataset_manifest.json"),
        static_runtime_artifacts=("solver_manifest.json", "dataset_manifest.json"),
        solves_study=True,
        extracts_results=False,
    ),
    "result_extraction_postprocess_validation": StageSpec(
        stage="result_extraction_postprocess_validation",
        script_name="matlab_c06_heat_rectangle_smoke.m",
        runtime_status_passed="matlab_livelink_result_extraction_passed",
        runtime_status_failed="matlab_livelink_result_extraction_failed",
        matlab_artifacts=("export_manifest.json", "probes.csv", "units.json"),
        static_runtime_artifacts=("export_manifest.json", "probes.csv", "units.json"),
        solves_study=True,
        extracts_results=True,
    ),
}


def _matlab_string(value: str) -> str:
    return str(value).replace("'", "''")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return None


def _env_path_check(env_name: str, required: bool, path_kind: str) -> dict[str, Any]:
    value = os.environ.get(env_name)
    configured = bool(value)
    exists = False
    if configured:
        path = Path(str(value))
        exists = path.is_file() if path_kind == "file" else path.is_dir()
    return {
        "env": env_name,
        "required": required,
        "path_kind": path_kind,
        "configured": configured,
        "exists": exists,
    }


def _collect_environment(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _env_path_check(config["matlab"]["executable_env"], True, "file"),
        _env_path_check(config["comsol"]["command_env"], True, "file"),
        _env_path_check(config["livelink"]["mli_dir_env"], True, "directory"),
        _env_path_check(config["comsol"]["mphserver_env"], False, "file"),
    ]


def _probe_rows(output_dir: Path) -> list[dict[str, str]]:
    path = output_dir / "probes.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _finite_probe_values(rows: list[dict[str, str]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        try:
            value = float(row.get("value", "nan"))
        except ValueError:
            continue
        if math.isfinite(value):
            values.append(value)
    return values


def _base_script_lines(config: dict[str, Any], spec: StageSpec) -> list[str]:
    case = config["heat_rectangle"]
    tags = case["tags"]
    width = case["geometry"]["width"]
    height = case["geometry"]["height"]
    mesh_size = int(case["mesh"]["auto_mesh_size"])
    lines = [
        "% Generated by science-capability-registry COMSOL C03-C06 smoke runner.",
        "% This script is a generated-rectangle smoke, not official model replay.",
        "mliDir = getenv('COMSOL_MLI_DIR');",
        "if strlength(mliDir) > 0",
        "    addpath(mliDir);",
        "end",
        "import com.comsol.model.*",
        "import com.comsol.model.util.*",
        "host = getenv('COMSOL_SERVER_HOST');",
        "portText = getenv('COMSOL_SERVER_PORT');",
        "if strlength(host) > 0",
        "    if strlength(portText) > 0",
        "        mphstart(host, str2double(portText));",
        "    else",
        "        mphstart(host);",
        "    end",
        "end",
        f"stageName = '{_matlab_string(spec.stage)}';",
        f"modelTag = '{_matlab_string(tags['model_tag'])}';",
        f"componentTag = '{_matlab_string(tags['component_tag'])}';",
        f"geometryTag = '{_matlab_string(tags['geometry_tag'])}';",
        f"rectangleTag = '{_matlab_string(tags['rectangle_tag'])}';",
        f"meshTag = '{_matlab_string(tags['mesh_tag'])}';",
        f"materialTag = '{_matlab_string(tags['material_tag'])}';",
        f"physicsTag = '{_matlab_string(tags['physics_tag'])}';",
        f"temperatureTag = '{_matlab_string(tags['temperature_boundary_tag'])}';",
        f"studyTag = '{_matlab_string(tags['study_tag'])}';",
        f"studyFeatureTag = '{_matlab_string(tags['study_feature_tag'])}';",
        "try",
        "    ModelUtil.remove(modelTag);",
        "catch",
        "end",
        "model = ModelUtil.create(modelTag);",
        f"model.param.set('{_matlab_string(case['geometry']['width_parameter'])}', '{_matlab_string(str(width))}');",
        f"model.param.set('{_matlab_string(case['geometry']['height_parameter'])}', '{_matlab_string(str(height))}');",
        "model.component.create(componentTag, true);",
        "model.component(componentTag).geom.create(geometryTag, 2);",
        "model.component(componentTag).geom(geometryTag).create(rectangleTag, 'Rectangle');",
        (
            "model.component(componentTag).geom(geometryTag).feature(rectangleTag).set('size', "
            f"{{'{_matlab_string(case['geometry']['width_parameter'])}', "
            f"'{_matlab_string(case['geometry']['height_parameter'])}'}});"
        ),
        "model.component(componentTag).geom(geometryTag).run;",
        "model.component(componentTag).mesh.create(meshTag);",
        f"model.component(componentTag).mesh(meshTag).autoMeshSize({mesh_size});",
        "model.component(componentTag).mesh(meshTag).run;",
        "geometryManifest = struct();",
        "geometryManifest.stage = stageName;",
        "geometryManifest.geometry_created = true;",
        "geometryManifest.geometry_type = 'generated_rectangle_2d';",
        "geometryManifest.width = " + str(float(width)) + ";",
        "geometryManifest.height = " + str(float(height)) + ";",
        "geometryManifest.dimension = 2;",
        "geometryManifest.solver_executed = false;",
        "meshManifest = struct();",
        "meshManifest.stage = stageName;",
        "meshManifest.mesh_created = true;",
        f"meshManifest.auto_mesh_size = {mesh_size};",
        "meshManifest.mesh_policy = 'COMSOL auto mesh size smoke';",
        "meshManifest.solver_executed = false;",
        "selectionMap = struct();",
        "selectionMap.stage = stageName;",
        "selectionMap.selection_role_count = 1;",
        "selectionMap.named_selections = {'all_rectangle_boundaries'};",
        "selectionMap.boundary_roles = {'fixed_temperature_all_boundaries'};",
        "selectionMap.generated_rectangle_only = true;",
        "fid = fopen('geometry_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(geometryManifest)); fclose(fid);",
        "fid = fopen('mesh_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(meshManifest)); fclose(fid);",
        "fid = fopen('selection_map.json', 'w'); fprintf(fid, '%s\\n', jsonencode(selectionMap)); fclose(fid);",
    ]
    if spec.stage != "geometry_mesh_import_contract":
        lines.extend(_physics_script_lines(config, spec))
    if spec.solves_study:
        lines.extend(_solve_script_lines(config))
    if spec.extracts_results:
        lines.extend(_export_script_lines(config))
    lines.extend(
        [
            "ModelUtil.remove(modelTag);",
            "",
        ]
    )
    return lines


def _physics_script_lines(config: dict[str, Any], spec: StageSpec) -> list[str]:
    case = config["heat_rectangle"]
    physics = case["physics"]
    return [
        f"model.component(componentTag).material.create(materialTag, '{_matlab_string(physics['material_type'])}');",
        "model.component(componentTag).material(materialTag).propertyGroup('def').set('thermalconductivity', {'1[W/(m*K)]'});",
        "model.component(componentTag).material(materialTag).propertyGroup('def').set('density', '1[kg/m^3]');",
        "model.component(componentTag).material(materialTag).propertyGroup('def').set('heatcapacity', '1[J/(kg*K)]');",
        f"model.component(componentTag).physics.create(physicsTag, '{_matlab_string(physics['interface_type'])}', geometryTag);",
        f"model.component(componentTag).physics(physicsTag).feature.create(temperatureTag, '{_matlab_string(physics['boundary_condition_type'])}', 1);",
        "model.component(componentTag).physics(physicsTag).feature(temperatureTag).selection.all;",
        f"model.component(componentTag).physics(physicsTag).feature(temperatureTag).set('T0', '{_matlab_string(physics['boundary_temperature'])}');",
        "physicsManifest = struct();",
        "physicsManifest.stage = stageName;",
        "physicsManifest.material_assigned = true;",
        "physicsManifest.physics_created = true;",
        "physicsManifest.physics_interface = '"
        + _matlab_string(physics["interface_type"])
        + "';",
        "physicsManifest.material_type = '"
        + _matlab_string(physics["material_type"])
        + "';",
        "physicsManifest.solver_executed = false;",
        "boundaryManifest = struct();",
        "boundaryManifest.stage = stageName;",
        "boundaryManifest.boundary_assignment_count = 1;",
        "boundaryManifest.missing_boundary_assignment_count = 0;",
        "boundaryManifest.assignment_scope = 'all generated rectangle boundaries';",
        "boundaryManifest.boundary_temperature = '"
        + _matlab_string(physics["boundary_temperature"])
        + "';",
        "boundaryManifest.solver_executed = false;",
        "unitPolicy = struct();",
        "unitPolicy.stage = stageName;",
        "unitPolicy.quantity = 'temperature';",
        "unitPolicy.expression = 'T';",
        "unitPolicy.unit = 'K';",
        "unitPolicy.missing_unit_count = 0;",
        "fid = fopen('physics_assignment_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(physicsManifest)); fclose(fid);",
        "fid = fopen('boundary_assignment_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(boundaryManifest)); fclose(fid);",
        "fid = fopen('unit_policy.json', 'w'); fprintf(fid, '%s\\n', jsonencode(unitPolicy)); fclose(fid);",
    ]


def _solve_script_lines(config: dict[str, Any]) -> list[str]:
    case = config["heat_rectangle"]
    return [
        "tic;",
        "model.study.create(studyTag);",
        f"model.study(studyTag).create(studyFeatureTag, '{_matlab_string(case['study']['study_type'])}');",
        "model.study(studyTag).run;",
        "elapsedSeconds = toc;",
        "centerTemperature = mphinterp(model, 'T', 'coord', [0.5; 0.25]);",
        "if isnumeric(centerTemperature)",
        "    centerValue = centerTemperature(1);",
        "else",
        "    centerValue = str2double(char(centerTemperature));",
        "end",
        "solverManifest = struct();",
        "solverManifest.stage = stageName;",
        "solverManifest.study_executed = true;",
        "solverManifest.solver_completed = true;",
        "solverManifest.elapsed_seconds = elapsedSeconds;",
        "solverManifest.temperature_probe = centerValue;",
        "datasetManifest = struct();",
        "datasetManifest.stage = stageName;",
        "datasetManifest.dataset_count = 1;",
        "datasetManifest.default_dataset = 'dset1';",
        "datasetManifest.has_solution_state = true;",
        "fid = fopen('solver_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(solverManifest)); fclose(fid);",
        "fid = fopen('dataset_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(datasetManifest)); fclose(fid);",
    ]


def _export_script_lines(config: dict[str, Any]) -> list[str]:
    probe = config["heat_rectangle"]["probes"][0]
    expected = float(probe["expected_value"])
    tolerance = float(probe["tolerance"])
    return [
        f"probeValue = mphinterp(model, '{_matlab_string(probe['expression'])}', 'coord', [{float(probe['x'])}; {float(probe['y'])}]);",
        "if isnumeric(probeValue)",
        "    numericProbeValue = probeValue(1);",
        "else",
        "    numericProbeValue = str2double(char(probeValue));",
        "end",
        "exportManifest = struct();",
        "exportManifest.stage = stageName;",
        "exportManifest.exported_probe_count = 1;",
        "exportManifest.expression = '" + _matlab_string(probe["expression"]) + "';",
        "exportManifest.unit = '" + _matlab_string(probe["unit"]) + "';",
        "exportManifest.finite_value_fraction = double(isfinite(numericProbeValue));",
        f"exportManifest.expected_value = {expected};",
        f"exportManifest.tolerance = {tolerance};",
        "exportManifest.abs_error = abs(numericProbeValue - exportManifest.expected_value);",
        "units = struct();",
        "units.temperature = 'K';",
        "units.missing_unit_count = 0;",
        "fid = fopen('export_manifest.json', 'w'); fprintf(fid, '%s\\n', jsonencode(exportManifest)); fclose(fid);",
        "fid = fopen('units.json', 'w'); fprintf(fid, '%s\\n', jsonencode(units)); fclose(fid);",
        "fid = fopen('probes.csv', 'w');",
        "fprintf(fid, 'probe,expression,x,y,value,unit,expected_value,abs_error\\n');",
        (
            f"fprintf(fid, '{_matlab_string(probe['name'])},{_matlab_string(probe['expression'])},"
            f"{float(probe['x'])},{float(probe['y'])},%.15g,{_matlab_string(probe['unit'])},"
            "%.15g,%.15g\\n', numericProbeValue, exportManifest.expected_value, exportManifest.abs_error);"
        ),
        "fclose(fid);",
    ]


def _script_text(config: dict[str, Any], spec: StageSpec) -> str:
    return "\n".join(_base_script_lines(config, spec))


def _write_script(config: dict[str, Any], output_dir: Path, spec: StageSpec) -> Path:
    script_path = output_dir / config["heat_rectangle"].get(
        "script_filename", spec.script_name
    )
    script_path.write_text(_script_text(config, spec), encoding="ascii")
    return script_path


def _write_placeholders(output_dir: Path, message: str) -> None:
    for name in ["stdout.txt", "stderr.txt"]:
        (output_dir / name).write_text(message + "\n", encoding="utf-8")


def _execute_matlab(config: dict[str, Any], output_dir: Path, script_path: Path) -> int:
    matlab_exe = Path(os.environ[config["matlab"]["executable_env"]])
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    script_expr = f"run('{script_path.resolve().as_posix()}')"
    with (
        stdout_path.open("w", encoding="utf-8", errors="replace") as stdout,
        stderr_path.open("w", encoding="utf-8", errors="replace") as stderr,
    ):
        result = subprocess.run(
            [str(matlab_exe), config["matlab"]["batch_argument"], script_expr],
            cwd=output_dir,
            stdout=stdout,
            stderr=stderr,
            timeout=float(config["backend"]["timeout_s"]),
            check=False,
        )
    return result.returncode


def _artifact_exists(output_dir: Path, name: str) -> bool:
    path = output_dir / name
    if name in {"stdout.txt", "stderr.txt"}:
        return path.exists()
    return path.exists() and path.stat().st_size > 0


def _build_metrics(
    config: dict[str, Any],
    output_dir: Path,
    script_path: Path,
    spec: StageSpec,
    environment_checks: list[dict[str, Any]],
    dry_run: bool,
    matlab_return_code: int | None,
) -> dict[str, Any]:
    env_summary = summarize_environment_checks(environment_checks)
    geometry = _load_json(output_dir / "geometry_manifest.json")
    mesh = _load_json(output_dir / "mesh_manifest.json")
    selection = _load_json(output_dir / "selection_map.json")
    physics = _load_json(output_dir / "physics_assignment_manifest.json")
    boundary = _load_json(output_dir / "boundary_assignment_manifest.json")
    unit_policy = _load_json(output_dir / "unit_policy.json")
    solver = _load_json(output_dir / "solver_manifest.json")
    dataset = _load_json(output_dir / "dataset_manifest.json")
    export = _load_json(output_dir / "export_manifest.json")
    units = _load_json(output_dir / "units.json")
    probe_rows = _probe_rows(output_dir)
    finite_values = _finite_probe_values(probe_rows)
    required_written = all(
        _artifact_exists(output_dir, name) for name in spec.matlab_artifacts
    )
    if dry_run:
        runtime_status = "dry_run_not_executed"
    elif matlab_return_code == 0 and required_written:
        runtime_status = spec.runtime_status_passed
    else:
        runtime_status = spec.runtime_status_failed
    finite_fraction = (len(finite_values) / len(probe_rows)) if probe_rows else 0.0
    expected = float(config["heat_rectangle"]["probes"][0]["expected_value"])
    max_abs_error = max(
        (abs(value - expected) for value in finite_values), default=None
    )
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "validated_config": True,
        "script_generated": script_path.exists(),
        "script_file": script_path.name,
        "environment_checks": environment_checks,
        "environment_summary": env_summary,
        "matlab_executed": matlab_return_code is not None,
        "matlab_return_code": matlab_return_code,
        "geometry_created": bool(geometry and geometry.get("geometry_created")),
        "mesh_created": bool(mesh and mesh.get("mesh_created")),
        "selection_role_count": (
            int(selection.get("selection_role_count", 0)) if selection else 0
        ),
        "material_assigned": bool(physics and physics.get("material_assigned")),
        "physics_created": bool(physics and physics.get("physics_created")),
        "boundary_assignment_count": (
            int(boundary.get("boundary_assignment_count", 0)) if boundary else 0
        ),
        "missing_boundary_assignment_count": (
            int(boundary.get("missing_boundary_assignment_count", 0)) if boundary else 0
        ),
        "missing_unit_count": (
            int((unit_policy or units or {}).get("missing_unit_count", 0))
            if unit_policy or units
            else 0
        ),
        "study_executed": bool(solver and solver.get("study_executed")),
        "solver_completed": bool(solver and solver.get("solver_completed")),
        "dataset_count": int(dataset.get("dataset_count", 0)) if dataset else 0,
        "exported_probe_count": (
            int(export.get("exported_probe_count", len(probe_rows)))
            if export
            else len(probe_rows)
        ),
        "finite_value_fraction": finite_fraction,
        "temperature_min": min(finite_values) if finite_values else None,
        "temperature_max": max(finite_values) if finite_values else None,
        "max_abs_temperature_error_K": max_abs_error,
        "solver_executed": bool(
            spec.solves_study and solver and solver.get("study_executed")
        ),
        "runtime_status": runtime_status,
    }


def _add_check(
    checks: list[dict[str, Any]], name: str, passed: bool, details: str
) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _validate_metrics(
    metrics: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
    spec: StageSpec,
    check_artifacts: bool,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    env_summary = metrics["environment_summary"]
    dry_run = metrics["runtime_status"] == "dry_run_not_executed"
    _add_check(
        checks,
        "config.validated",
        bool(metrics["validated_config"]),
        "configuration schema accepted",
    )
    _add_check(
        checks,
        "script.generated",
        bool(metrics["script_generated"]),
        metrics["script_file"],
    )
    if not dry_run:
        _add_check(
            checks,
            "geometry.created",
            bool(metrics["geometry_created"]),
            str(metrics["geometry_created"]),
        )
        _add_check(
            checks,
            "mesh.created",
            bool(metrics["mesh_created"]),
            str(metrics["mesh_created"]),
        )
        if spec.stage == "geometry_mesh_import_contract":
            _add_check(
                checks,
                "selection.roles_declared",
                metrics["selection_role_count"] >= 1,
                str(metrics["selection_role_count"]),
            )
            _add_check(
                checks,
                "solver.not_executed",
                metrics["solver_executed"] is False,
                str(metrics["solver_executed"]),
            )
        if spec.stage == "physics_boundary_assignment_contract":
            _add_check(
                checks,
                "physics.created",
                bool(metrics["physics_created"]),
                str(metrics["physics_created"]),
            )
            _add_check(
                checks,
                "material.assigned",
                bool(metrics["material_assigned"]),
                str(metrics["material_assigned"]),
            )
            _add_check(
                checks,
                "boundary.assignments_complete",
                metrics["missing_boundary_assignment_count"] == 0,
                str(metrics["missing_boundary_assignment_count"]),
            )
            _add_check(
                checks,
                "units.present",
                metrics["missing_unit_count"] == 0,
                str(metrics["missing_unit_count"]),
            )
            _add_check(
                checks,
                "solver.not_executed",
                metrics["solver_executed"] is False,
                str(metrics["solver_executed"]),
            )
        if spec.stage == "study_run_solver_smoke":
            _add_check(
                checks,
                "solver.completed",
                bool(metrics["solver_completed"]),
                str(metrics["solver_completed"]),
            )
            _add_check(
                checks,
                "dataset.present",
                metrics["dataset_count"] >= 1,
                str(metrics["dataset_count"]),
            )
        if spec.stage == "result_extraction_postprocess_validation":
            _add_check(
                checks,
                "solver.completed",
                bool(metrics["solver_completed"]),
                str(metrics["solver_completed"]),
            )
            _add_check(
                checks,
                "probe.exported",
                metrics["exported_probe_count"] >= 1,
                str(metrics["exported_probe_count"]),
            )
            _add_check(
                checks,
                "probe.values_finite",
                metrics["finite_value_fraction"] >= 1.0,
                str(metrics["finite_value_fraction"]),
            )
            _add_check(
                checks,
                "units.present",
                metrics["missing_unit_count"] == 0,
                str(metrics["missing_unit_count"]),
            )
            tolerance = float(config["heat_rectangle"]["probes"][0]["tolerance"])
            error_value = metrics["max_abs_temperature_error_K"]
            _add_check(
                checks,
                "probe.expected_constant_temperature",
                error_value is not None and error_value <= tolerance,
                str(error_value),
            )
        _add_check(
            checks,
            "environment.required_configured",
            bool(env_summary["all_required_configured"]),
            f"{env_summary['required_configured_count']} of {env_summary['required_count']}",
        )
        if config["validation"]["require_path_exists"]:
            _add_check(
                checks,
                "environment.required_paths_exist",
                bool(env_summary["all_required_paths_exist"]),
                f"{env_summary['required_existing_count']} of {env_summary['required_count']}",
            )
        if config["validation"]["require_matlab_execution"]:
            _add_check(
                checks,
                "matlab.return_code",
                metrics.get("matlab_return_code") == 0,
                str(metrics.get("matlab_return_code")),
            )
    if check_artifacts:
        artifact_targets = [
            metrics["script_file"],
            "manifest.json",
            "metrics.json",
            "validation.json",
            "validation_report.md",
        ]
        if not dry_run:
            artifact_targets.extend(config["validation"]["required_artifacts"])
            artifact_targets.extend(["stdout.txt", "stderr.txt"])
        for rel_path in artifact_targets:
            _add_check(
                checks,
                f"artifact.exists.{rel_path}",
                _artifact_exists(output_dir, rel_path),
                rel_path,
            )
    return {
        "passed": all(item["passed"] for item in checks),
        "gate": "static-readiness" if dry_run else config["validation"]["gate"],
        "scope": _validation_scope(spec, dry_run),
        "checks": checks,
        "details": {
            "runtime_status": metrics["runtime_status"],
            "no_claims": config["validation"]["no_claims"],
        },
    }


def _validation_scope(spec: StageSpec, dry_run: bool) -> str:
    if dry_run:
        return f"COMSOL {spec.stage} generated-script dry run; MATLAB and COMSOL were not executed"
    return f"COMSOL {spec.stage} MATLAB LiveLink generated heat-rectangle smoke"


def _write_report(
    path: str | Path,
    config: dict[str, Any],
    metrics: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    env_summary = metrics["environment_summary"]
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# COMSOL {config['asset_id']} {config['case_id']} validation report",
        "",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime status: {metrics['runtime_status']}",
        f"- required env configured: {env_summary['required_configured_count']} / {env_summary['required_count']}",
        f"- required paths existing: {env_summary['required_existing_count']} / {env_summary['required_count']}",
        f"- MATLAB executed: {metrics['matlab_executed']}",
        f"- MATLAB return code: {metrics['matlab_return_code']}",
        f"- solver executed: {metrics['solver_executed']}",
        f"- finite value fraction: {metrics['finite_value_fraction']}",
        "",
        "## Checks",
        "",
    ]
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(["", "## Scope", "", validation["scope"]])
    lines.extend(["", "## No Claims", ""])
    for claim in config["validation"]["no_claims"]:
        lines.append(f"- {claim}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_manifest(
    config: dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
    metrics: dict[str, Any],
    validation: dict[str, Any],
    schema_id: str,
) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "asset_id": config["asset_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": schema_id,
        "validated_config": True,
        "output_dir": str(output_dir),
        "runtime_profile": config["comsol"]["runtime_profile"],
        "runtime_profile_config": config["comsol"]["runtime_profile_config"],
        "backend": config["backend"],
        "contract": config["contract"],
        "heat_rectangle": config["heat_rectangle"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "metrics": metrics,
        "validation": validation,
        "scope": validation["scope"],
    }


def _write_dry_run_stage_artifacts(
    config: dict[str, Any], output_dir: Path, spec: StageSpec
) -> None:
    for name in spec.static_runtime_artifacts:
        path = output_dir / name
        if path.suffix.lower() == ".csv":
            path.write_text(
                "probe,expression,x,y,value,unit,expected_value,abs_error\n",
                encoding="utf-8",
            )
        else:
            payload = {
                "capability_id": config["capability_id"],
                "case_id": config["case_id"],
                "stage": spec.stage,
                "artifact_path": name,
                "runtime_executed": False,
                "generated_script_contract": True,
                "no_claims": config["validation"]["no_claims"],
            }
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_heat_rectangle_stage(
    schema_path: str | Path,
    schema_id: str,
    stage: str,
    *,
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
    backend: str | None = None,
) -> dict[str, Any]:
    if stage not in STAGE_SPECS:
        raise ValueError(f"Unknown COMSOL heat-rectangle stage: {stage}")
    spec = STAGE_SPECS[stage]
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_static_config(config_path, schema_path)
    else:
        config = validate_static_config(config, schema_path)
    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_static_config(config, schema_path)
    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        return run_static_contract(
            schema_path,
            schema_id,
            config_path=config_path,
            config=config if config_path is None else None,
            output_dir=output_dir,
            dry_run=dry_run,
        )
    if backend_type != "matlab_livelink_heat_rectangle_smoke":
        raise NotImplementedError(
            f"COMSOL backend {backend_type!r} is not implemented for {stage}."
        )

    output_path = (
        Path(output_dir)
        if output_dir is not None
        else repo_relative_path(config["outputs"]["output_dir"])
    )
    output_path.mkdir(parents=True, exist_ok=True)
    script_path = _write_script(config, output_path, spec)
    environment_checks = _collect_environment(config)
    env_summary = summarize_environment_checks(environment_checks)
    matlab_return_code: int | None = None
    generated_files = [
        script_path.name,
        "stdout.txt",
        "stderr.txt",
        "metrics.json",
        "validation.json",
        "validation_report.md",
        "manifest.json",
    ]
    if dry_run:
        _write_placeholders(
            output_path, "dry-run placeholder; MATLAB and COMSOL were not executed."
        )
        _write_dry_run_stage_artifacts(config, output_path, spec)
        generated_files.extend(spec.static_runtime_artifacts)
    elif env_summary["all_required_paths_exist"]:
        matlab_return_code = _execute_matlab(config, output_path, script_path)
        for name in spec.matlab_artifacts:
            if (output_path / name).exists():
                generated_files.append(name)
    else:
        _write_placeholders(
            output_path,
            "runtime profile is incomplete; MATLAB and COMSOL were not executed.",
        )

    metrics = _build_metrics(
        config,
        output_path,
        script_path,
        spec,
        environment_checks,
        dry_run,
        matlab_return_code,
    )
    validation = _validate_metrics(
        metrics, config, output_path, spec, check_artifacts=False
    )
    (output_path / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (output_path / "validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    _write_report(output_path / "validation_report.md", config, metrics, validation)
    manifest = _build_manifest(
        config, output_path, generated_files, metrics, validation, schema_id
    )
    (output_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    validation = _validate_metrics(
        metrics, config, output_path, spec, check_artifacts=True
    )
    manifest["validation"] = validation
    manifest["scope"] = validation["scope"]
    (output_path / "validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    _write_report(output_path / "validation_report.md", config, metrics, validation)
    (output_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest
