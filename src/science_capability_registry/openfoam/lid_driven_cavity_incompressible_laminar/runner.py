"""Runner for the OpenFOAM C01 lid-driven cavity capability."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import load_case_config, repo_relative_path, validate_case_config
from .runtime import (
    build_runtime_metrics,
    execute_wsl_runtime,
    validate_runtime_metrics,
    write_runtime_report,
)
from .validation import validate_manifest


def _foam_header(class_name: str, object_name: str) -> str:
    return (
        "FoamFile\n"
        "{\n"
        "    version     2.0;\n"
        "    format      ascii;\n"
        f"    class       {class_name};\n"
        f"    object      {object_name};\n"
        "}\n"
    )


def _boundary_entry(boundary: dict[str, str]) -> str:
    lines = [f"        type            {boundary['type']};"]
    if "value" in boundary:
        lines.append(f"        value           {boundary['value']};")
    return "\n".join(lines)


def _field_file(name: str, field: dict[str, Any]) -> str:
    boundary_lines = []
    for patch_name, boundary in field["boundaries"].items():
        boundary_lines.append(
            f"    {patch_name}\n"
            "    {\n"
            f"{_boundary_entry(boundary)}\n"
            "    }"
        )
    return (
        f"{_foam_header(field['class'], name)}\n"
        f"dimensions      {field['dimensions']};\n\n"
        f"internalField   {field['internal_field']};\n\n"
        "boundaryField\n"
        "{\n"
        + "\n".join(boundary_lines)
        + "\n}\n"
    )


def _transport_properties(config: dict[str, Any]) -> str:
    nu = config["material"]["kinematic_viscosity_m2_s"]
    return (
        f"{_foam_header('dictionary', 'transportProperties')}\n"
        f"nu              [0 2 -1 0 0 0 0] {nu};\n"
    )


def _block_mesh_dict(config: dict[str, Any]) -> str:
    cells = config["mesh"]["cells"]
    grading = config["mesh"]["simple_grading"]
    scale = config["geometry"]["cavity_side_length_m"]
    relative_thickness = config["geometry"]["thickness_m"] / scale
    return (
        f"{_foam_header('dictionary', 'blockMeshDict')}\n"
        f"scale           {scale};\n\n"
        "vertices\n"
        "(\n"
        "    (0 0 0)\n"
        "    (1 0 0)\n"
        "    (1 1 0)\n"
        "    (0 1 0)\n"
        f"    (0 0 {relative_thickness:g})\n"
        f"    (1 0 {relative_thickness:g})\n"
        f"    (1 1 {relative_thickness:g})\n"
        f"    (0 1 {relative_thickness:g})\n"
        ");\n\n"
        "blocks\n"
        "(\n"
        f"    hex (0 1 2 3 4 5 6 7) ({cells[0]} {cells[1]} {cells[2]}) "
        f"simpleGrading ({grading[0]} {grading[1]} {grading[2]})\n"
        ");\n\n"
        "edges\n"
        "(\n"
        ");\n\n"
        "boundary\n"
        "(\n"
        "    movingWall\n"
        "    {\n"
        "        type wall;\n"
        "        faces\n"
        "        (\n"
        "            (3 7 6 2)\n"
        "        );\n"
        "    }\n"
        "    fixedWalls\n"
        "    {\n"
        "        type wall;\n"
        "        faces\n"
        "        (\n"
        "            (0 4 7 3)\n"
        "            (2 6 5 1)\n"
        "            (1 5 4 0)\n"
        "        );\n"
        "    }\n"
        "    frontAndBack\n"
        "    {\n"
        "        type empty;\n"
        "        faces\n"
        "        (\n"
        "            (0 3 2 1)\n"
        "            (4 5 6 7)\n"
        "        );\n"
        "    }\n"
        ");\n\n"
        "mergePatchPairs\n"
        "(\n"
        ");\n"
    )


def _control_dict(config: dict[str, Any]) -> str:
    control = config["numerics"]["control"]
    solver = config["solver"]["name"]
    return (
        f"{_foam_header('dictionary', 'controlDict')}\n"
        f"application     {solver};\n\n"
        "startFrom       startTime;\n"
        f"startTime       {control['start_time_s']};\n\n"
        "stopAt          endTime;\n"
        f"endTime         {control['end_time_s']};\n\n"
        f"deltaT          {control['delta_t_s']};\n\n"
        "writeControl    timeStep;\n"
        f"writeInterval   {control['write_interval']};\n"
        "purgeWrite      0;\n"
        "writeFormat     ascii;\n"
        "writePrecision  6;\n"
        "writeCompression off;\n"
        "timeFormat      general;\n"
        "timePrecision   6;\n"
        "runTimeModifiable true;\n"
    )


def _fv_schemes(config: dict[str, Any]) -> str:
    schemes = config["numerics"]["fv_schemes"]
    return (
        f"{_foam_header('dictionary', 'fvSchemes')}\n"
        "ddtSchemes\n"
        "{\n"
        f"    default         {schemes['ddt']};\n"
        "}\n\n"
        "gradSchemes\n"
        "{\n"
        f"    default         {schemes['grad']};\n"
        "}\n\n"
        "divSchemes\n"
        "{\n"
        f"    div(phi,U)      {schemes['div_phi_U']};\n"
        "}\n\n"
        "laplacianSchemes\n"
        "{\n"
        f"    default         {schemes['laplacian']};\n"
        "}\n\n"
        "interpolationSchemes\n"
        "{\n"
        f"    default         {schemes['interpolation']};\n"
        "}\n\n"
        "snGradSchemes\n"
        "{\n"
        f"    default         {schemes['sn_grad']};\n"
        "}\n"
    )


def _solver_block(config: dict[str, Any], key: str) -> str:
    solver = config["numerics"]["fv_solution"][key]
    lines = [
        "    {",
        f"        solver          {solver['solver']};",
    ]
    if "preconditioner" in solver:
        lines.append(f"        preconditioner  {solver['preconditioner']};")
    if "smoother" in solver:
        lines.append(f"        smoother        {solver['smoother']};")
    lines.extend(
        [
            f"        tolerance       {solver['tolerance']};",
            f"        relTol          {solver['relTol']};",
            "    }",
        ]
    )
    return "\n".join(lines)


def _fv_solution(config: dict[str, Any]) -> str:
    solution = config["numerics"]["fv_solution"]
    piso = solution["piso"]
    p_final = solution["p_final_solver"]
    return (
        f"{_foam_header('dictionary', 'fvSolution')}\n"
        "solvers\n"
        "{\n"
        "    p\n"
        f"{_solver_block(config, 'p_solver')}\n"
        "\n"
        "    pFinal\n"
        "    {\n"
        f"        ${p_final['base']};\n"
        f"        relTol          {p_final['relTol']};\n"
        "    }\n"
        "\n"
        "    U\n"
        f"{_solver_block(config, 'U_solver')}\n"
        "}\n\n"
        "PISO\n"
        "{\n"
        f"    nCorrectors     {piso['nCorrectors']};\n"
        f"    nNonOrthogonalCorrectors {piso['nNonOrthogonalCorrectors']};\n"
        f"    pRefCell        {piso['pRefCell']};\n"
        f"    pRefValue       {piso['pRefValue']};\n"
        "}\n"
    )


def _case_files(config: dict[str, Any]) -> dict[str, str]:
    return {
        "case/0/U": _field_file("U", config["fields"]["U"]),
        "case/0/p": _field_file("p", config["fields"]["p"]),
        "case/constant/transportProperties": _transport_properties(config),
        "case/system/blockMeshDict": _block_mesh_dict(config),
        "case/system/controlDict": _control_dict(config),
        "case/system/fvSchemes": _fv_schemes(config),
        "case/system/fvSolution": _fv_solution(config),
    }


def _write_case_files(output_dir: Path, config: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for rel_path, content in _case_files(config).items():
        path = output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(rel_path)
    return written


def _build_manifest(
    config: dict[str, Any],
    output_dir: Path,
    generated_files: list[str],
) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": "schemas/openfoam_C01_lid_driven_cavity_incompressible_laminar.schema.json",
        "output_dir": str(output_dir),
        "openfoam": config["openfoam"],
        "backend": config["backend"],
        "solver": config["solver"],
        "generated_files": generated_files,
        "mesh_commands": ["blockMesh"],
        "solver_commands": [config["solver"]["name"]],
        "postprocess_commands": ["python:write_centerline_profiles"],
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
    """Generate an OpenFOAM C01 case and optionally execute it through a backend."""
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_case_config(config_path)
    else:
        config = validate_case_config(config)

    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_case_config(config)

    resolved_output_dir = (
        Path(output_dir)
        if output_dir is not None
        else repo_relative_path(config["outputs"]["output_dir"])
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = _write_case_files(resolved_output_dir, config)
    manifest = _build_manifest(config, resolved_output_dir, generated_files)

    if dry_run:
        validation = validate_manifest(manifest, config, resolved_output_dir)
        manifest["validation"] = validation
        manifest_path = resolved_output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("OpenFOAM C01 dry_run_only backend requires dry_run=True.")
    if backend_type != "wsl":
        raise NotImplementedError(f"OpenFOAM C01 backend {backend_type!r} is not implemented.")

    manifest["scope"] = "local WSL OpenFOAM runtime smoke with generated case files"
    runtime = execute_wsl_runtime(config, resolved_output_dir)
    metrics = build_runtime_metrics(config, resolved_output_dir, runtime)
    metrics_path = resolved_output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_runtime_metrics(metrics, config, resolved_output_dir)
    validation_path = resolved_output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_runtime_report(config, metrics, validation, resolved_output_dir)

    manifest["runtime"] = {
        "backend": runtime["backend"],
        "wsl_distro": runtime["wsl_distro"],
        "bashrc_path": runtime["bashrc_path"],
        "profile_env": runtime["profile_env"],
        "commands": runtime["commands"],
        "metrics_json": str(metrics_path),
        "validation_json": str(validation_path),
    }
    manifest["validation"] = validation
    manifest_path = resolved_output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Stable package entrypoint for dry-run workflow callers."""
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
