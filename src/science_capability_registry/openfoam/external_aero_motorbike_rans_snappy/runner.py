"""Runner for the OpenFOAM C04 external-aero motorBike capability."""

from __future__ import annotations

import json
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import (
    copy_template_case,
    map_windows_path_to_wsl,
    resolve_runtime_identity,
    run_wsl,
)

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import execute_wsl_runtime, write_runtime_outputs
from .validation import validate_manifest


def _replace_assignment(text: str, keyword: str, value: str) -> str:
    pattern = rf"({re.escape(keyword)}\s+)[^;]+;"
    return re.sub(pattern, rf"\g<1>{value};", text, count=1)


def _replace_active_assignment(text: str, keyword: str, value: str) -> str:
    pattern = rf"(?m)^([ \t]*)(?!//)(?!/\*)({re.escape(keyword)}\s+)[^;]+;"
    updated, count = re.subn(pattern, lambda match: f"{match.group(1)}{match.group(2)}{value};", text, count=1)
    if count:
        return updated
    commented = re.search(rf"(?m)^([ \t]*)//-?\s*{re.escape(keyword)}\s+[^;]+;", text)
    if commented:
        insert_at = commented.end()
        return text[:insert_at] + f"\n{commented.group(1)}{keyword} {value};" + text[insert_at:]
    raise ValueError(f"Active OpenFOAM assignment {keyword!r} not found and no commented template entry is available.")


def _upsert_active_assignment(text: str, keyword: str, value: str) -> str:
    try:
        return _replace_active_assignment(text, keyword, value)
    except ValueError:
        return text.rstrip() + f"\n{keyword} {value};\n"


def _vector_text(values: list[float]) -> str:
    return f"({values[0]:g} {values[1]:g} {values[2]:g})"


def _replace_vector_assignment(text: str, keyword: str, vector: list[float]) -> str:
    return _replace_assignment(text, keyword, _vector_text(vector))


def _foam_bool(value: bool) -> str:
    return "true" if value else "false"


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _prepare_zero_dir(case_dir: Path, zero_source_dir: str) -> None:
    target = case_dir / "0"
    source = case_dir / zero_source_dir
    if target.exists():
        shutil.rmtree(target)
    if not source.exists():
        raise FileNotFoundError(f"OpenFOAM zero source directory not found: {source}")
    shutil.copytree(source, target)


def _copy_geometry_resource(output_dir: Path, config: dict[str, Any], distro: str, timeout_s: float) -> None:
    target = output_dir / "case" / config["template"]["geometry_target_path"]
    target_parent_linux = map_windows_path_to_wsl(target.parent, distro, timeout_s)
    source = config["template"]["geometry_resource_path"]
    script = (
        f"test -f {shlex.quote(source)} && "
        f"mkdir -p {shlex.quote(target_parent_linux)} && "
        f"cp -f {shlex.quote(source)} {shlex.quote(target_parent_linux)}/"
    )
    result = run_wsl(distro, script, timeout_s)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to copy motorBike geometry resource: {detail}")


def _patch_control_dict(case_dir: Path, config: dict[str, Any]) -> None:
    control = case_dir / "system" / "controlDict"
    text = control.read_text(encoding="utf-8")
    text = _replace_assignment(text, "endTime", f"{config['numerics']['control']['end_time_iterations']:g}")
    text = _replace_assignment(text, "writeInterval", f"{config['numerics']['control']['write_interval']:g}")
    text = _replace_assignment(text, "writeFormat", "ascii")
    functions_block = "functions\n{\n    #include \"forceCoeffs\"\n}"
    if not config["function_objects"]["force_coefficients"]["enabled"]:
        functions_block = "functions\n{}"
    text = re.sub(
        r"functions\s*\{.*?\n\}",
        functions_block,
        text,
        count=1,
        flags=re.DOTALL,
    )
    _write_text(control, text)


def _patch_snappy_dict(case_dir: Path, config: dict[str, Any]) -> None:
    snappy_path = case_dir / "system" / "snappyHexMeshDict"
    text = snappy_path.read_text(encoding="utf-8")
    snappy = config["mesh"]["snappy"]
    text = _replace_assignment(text, "castellatedMesh", _foam_bool(snappy["castellated_mesh"]))
    text = _replace_assignment(text, "snap", _foam_bool(snappy["snap"]))
    text = _replace_assignment(text, "addLayers", _foam_bool(snappy["add_layers"]))
    text = re.sub(
        r'(file\s+"motorBike\.eMesh"\s*;\s*level\s+)\d+(;)',
        rf"\g<1>{int(snappy['feature_level'])}\2",
        text,
        count=1,
    )
    surface_level = f"({int(snappy['surface_refinement_level'][0])} {int(snappy['surface_refinement_level'][1])})"
    text = re.sub(
        r"(motorBike\s*\{.*?level\s+)\([^)]+\)(;)",
        rf"\g<1>{surface_level}\2",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(refinementBox\s*\{.*?levels\s+\(\(1E15\s+)\d+(\)\);)",
        rf"\g<1>{int(snappy['refinement_box_level'])}\2",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = _replace_assignment(text, "nSurfaceLayers", str(int(snappy["n_surface_layers"])))
    snap_controls = snappy.get("snap_controls", {})
    assignment_map = {
        "n_smooth_patch": ("nSmoothPatch", lambda value: str(int(value))),
        "tolerance": ("tolerance", lambda value: f"{float(value):g}"),
        "n_solve_iter": ("nSolveIter", lambda value: str(int(value))),
        "n_relax_iter": ("nRelaxIter", lambda value: str(int(value))),
        "n_feature_snap_iter": ("nFeatureSnapIter", lambda value: str(int(value))),
        "implicit_feature_snap": ("implicitFeatureSnap", _foam_bool),
        "explicit_feature_snap": ("explicitFeatureSnap", _foam_bool),
        "multi_region_feature_snap": ("multiRegionFeatureSnap", _foam_bool),
    }
    for config_key, (foam_key, formatter) in assignment_map.items():
        if config_key in snap_controls:
            text = _replace_active_assignment(text, foam_key, formatter(snap_controls[config_key]))
    _write_text(snappy_path, text)


def _patch_mesh_quality_dict(case_dir: Path, config: dict[str, Any]) -> None:
    quality_path = case_dir / "system" / "meshQualityDict"
    text = quality_path.read_text(encoding="utf-8")
    quality = config["mesh"]["quality"]
    text = _replace_active_assignment(text, "minFaceWeight", f"{quality['min_face_weight']:g}")
    if "max_internal_skewness" in quality:
        text = _upsert_active_assignment(text, "maxInternalSkewness", f"{quality['max_internal_skewness']:g}")
    if "max_boundary_skewness" in quality:
        text = _upsert_active_assignment(text, "maxBoundarySkewness", f"{quality['max_boundary_skewness']:g}")
    if "min_twist" in quality:
        text = _upsert_active_assignment(text, "minTwist", f"{quality['min_twist']:g}")
    _write_text(quality_path, text)


def _patch_case_files(output_dir: Path, config: dict[str, Any]) -> None:
    case_dir = output_dir / "case"
    _prepare_zero_dir(case_dir, config["template"]["zero_source_dir"])
    _patch_control_dict(case_dir, config)
    _patch_snappy_dict(case_dir, config)
    _patch_mesh_quality_dict(case_dir, config)

    initial = case_dir / "0" / "include" / "initialConditions"
    initial_text = initial.read_text(encoding="utf-8")
    initial_text = _replace_vector_assignment(initial_text, "flowVelocity", [float(config["material"]["inlet_velocity_m_s"]), 0.0, 0.0])
    initial_text = _replace_assignment(initial_text, "pressure", "0")
    initial_text = _replace_assignment(initial_text, "turbulentKE", f"{config['turbulence']['turbulent_kinetic_energy_m2_s2']:g}")
    initial_text = _replace_assignment(initial_text, "turbulentOmega", f"{config['turbulence']['specific_dissipation_rate_1_s']:g}")
    _write_text(initial, initial_text)

    transport = case_dir / "constant" / "transportProperties"
    transport_text = transport.read_text(encoding="utf-8")
    transport_text = _replace_assignment(transport_text, "nu", f"{config['material']['kinematic_viscosity_m2_s']:g}")
    _write_text(transport, transport_text)

    force = case_dir / "system" / "forceCoeffs"
    force_text = force.read_text(encoding="utf-8")
    force_text = _replace_assignment(force_text, "rhoInf", f"{config['material']['density_kg_m3']:g}")
    force_text = _replace_assignment(force_text, "magUInf", f"{config['material']['inlet_velocity_m_s']:g}")
    force_text = _replace_assignment(force_text, "lRef", f"{config['geometry']['reference_length_m']:g}")
    force_text = _replace_assignment(force_text, "Aref", f"{config['geometry']['reference_area_m2']:g}")
    force_text = _replace_vector_assignment(force_text, "liftDir", [float(value) for value in config["geometry"]["lift_direction"]])
    force_text = _replace_vector_assignment(force_text, "dragDir", [float(value) for value in config["geometry"]["drag_direction"]])
    force_text = _replace_vector_assignment(force_text, "CofR", [float(value) for value in config["geometry"]["centre_of_rotation_m"]])
    _write_text(force, force_text)


def _generated_files(output_dir: Path) -> list[str]:
    return [path.relative_to(output_dir).as_posix() for path in sorted((output_dir / "case").rglob("*")) if path.is_file()]


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    postprocess_commands = []
    if config["function_objects"]["force_coefficients"]["enabled"]:
        postprocess_commands.append("python:write_force_metrics")
    if config["function_objects"]["y_plus"]["required"]:
        postprocess_commands.append("python:write_y_plus_summary")
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C04_external_aero_motorbike_rans_snappy.schema.json",
        "output_dir": str(output_dir),
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "template": config["template"],
        "geometry": config["geometry"],
        "mesh": config["mesh"],
        "material": config["material"],
        "turbulence": config["turbulence"],
        "fields": config["fields"],
        "boundary_conditions": config["boundary_conditions"],
        "numerics": config["numerics"],
        "function_objects": config["function_objects"],
        "postprocess": config["postprocess"],
        "generated_files": generated_files,
        "mesh_commands": config["mesh"]["workflow"],
        "solver_commands": config["solver"]["command_sequence"],
        "postprocess_commands": postprocess_commands,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": "dry-run manifest and generated case files; no OpenFOAM solver execution",
    }


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
    backend: str | None = None,
) -> dict[str, Any]:
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)
    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_case_config(config)

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    runtime_identity = resolve_runtime_identity(config)
    timeout_s = runtime_identity["timeout_s"]
    distro = runtime_identity["wsl_distro"]
    copy_template_case(distro, config["template"]["source_path"], resolved_output_dir, timeout_s)
    _copy_geometry_resource(resolved_output_dir, config, distro, timeout_s)
    _patch_case_files(resolved_output_dir, config)
    generated_files = _generated_files(resolved_output_dir)
    manifest = _build_manifest(config, resolved_output_dir, generated_files)

    if dry_run:
        validation = validate_manifest(manifest, config, resolved_output_dir)
        manifest["validation"] = validation
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("OpenFOAM C04 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C04 backend {backend_type!r} is not implemented.")

    manifest["scope"] = "local WSL OpenFOAM runtime for motorBike snappyHexMesh simpleFoam template case"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    outputs = write_runtime_outputs(config, resolved_output_dir, runtime)
    manifest["runtime"] = {
        "backend": runtime["backend"],
        "wsl_distro": runtime["wsl_distro"],
        "bashrc_path": runtime["bashrc_path"],
        "profile_env": runtime["profile_env"],
        "commands": runtime["commands"],
        "metrics_json": str(outputs["metrics_path"]),
        "validation_json": str(outputs["validation_path"]),
    }
    manifest["validation"] = outputs["validation"]
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
