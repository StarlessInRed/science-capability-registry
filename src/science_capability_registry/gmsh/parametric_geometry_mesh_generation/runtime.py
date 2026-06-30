"""Gmsh Python API runtime for C01."""

from __future__ import annotations

import json
import math
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import map_windows_path_to_wsl, run_wsl

from .report import write_validation_report
from .validation import validate_mesh_summary


def _import_gmsh() -> Any:
    try:
        import gmsh
    except ModuleNotFoundError as exc:
        raise RuntimeError("The gmsh Python package is required for backend.type=python_api.") from exc
    return gmsh


def _triangle_quality(points: list[tuple[float, float, float]]) -> float:
    a = math.dist(points[0], points[1])
    b = math.dist(points[1], points[2])
    c = math.dist(points[2], points[0])
    semiperimeter = 0.5 * (a + b + c)
    area_square = semiperimeter * (semiperimeter - a) * (semiperimeter - b) * (semiperimeter - c)
    if area_square <= 0.0:
        return 0.0
    area = math.sqrt(area_square)
    denominator = a * a + b * b + c * c
    if denominator <= 0.0:
        return 0.0
    return 4.0 * math.sqrt(3.0) * area / denominator


def _summarize_mesh(gmsh: Any, dimension: int) -> dict[str, Any]:
    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    node_map: dict[int, tuple[float, float, float]] = {}
    finite = True
    for index, tag in enumerate(node_tags):
        point = (float(coords[3 * index]), float(coords[3 * index + 1]), float(coords[3 * index + 2]))
        finite = finite and all(math.isfinite(value) for value in point)
        node_map[int(tag)] = point

    element_count = 0
    element_quality_tags: list[int] = []
    fallback_triangle_qualities: list[float] = []
    for element_type, element_tags, element_nodes in zip(*gmsh.model.mesh.getElements(dimension)):
        name, _, _, node_count, _, _ = gmsh.model.mesh.getElementProperties(element_type)
        element_count += len(element_tags)
        element_quality_tags.extend(int(tag) for tag in element_tags)
        if node_count >= 3 and "triangle" in name.lower():
            for offset in range(0, len(element_nodes), node_count):
                tags = [int(tag) for tag in element_nodes[offset : offset + 3]]
                if all(tag in node_map for tag in tags):
                    fallback_triangle_qualities.append(_triangle_quality([node_map[tag] for tag in tags]))

    groups: dict[str, dict[str, Any]] = {}
    for dimension, tag in gmsh.model.getPhysicalGroups():
        name = gmsh.model.getPhysicalName(dimension, tag)
        entities = gmsh.model.getEntitiesForPhysicalGroup(dimension, tag)
        groups[name] = {
            "dimension": int(dimension),
            "tag": int(tag),
            "entity_count": len(entities),
            "entities": [int(entity) for entity in entities],
        }
    if element_quality_tags:
        qualities = [float(value) for value in gmsh.model.mesh.getElementQualities(element_quality_tags)]
        quality_metric = "gmsh_minSICN"
    else:
        qualities = fallback_triangle_qualities
        quality_metric = "linear_triangle_quality_proxy"
    min_quality = min(qualities) if qualities else 1.0
    return {
        "node_count": len(node_tags),
        "element_count": element_count,
        "coordinates_finite": finite,
        "physical_groups": groups,
        "quality": {
            "metric": quality_metric,
            "sample_count": len(qualities),
            "min_quality_proxy": min_quality,
        },
    }


def _foam_list_count(path: Path) -> int | None:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _parse_boundary_names(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    names: list[str] = []
    inside_entries = False
    for index, line in enumerate(lines):
        stripped = line.strip().strip('"')
        if not inside_entries:
            if stripped == "(":
                inside_entries = True
            continue
        if stripped == ")":
            break
        if not re.match(r"^[A-Za-z0-9_./-]+$", stripped):
            continue
        next_tokens = [candidate.strip() for candidate in lines[index + 1 : index + 4] if candidate.strip()]
        if next_tokens and next_tokens[0] == "{":
            names.append(stripped)
    return names


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


def _foam_vector(values: list[float] | tuple[float, float, float]) -> str:
    return f"({float(values[0]):g} {float(values[1]):g} {float(values[2]):g})"


def _physical_surface_roles(config: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (item["name"], item["role"])
        for item in config["physical_groups"]
        if int(item["dimension"]) == 2
    ]


def _field_file(name: str, dimensions: str, internal_field: str, boundary_entries: dict[str, dict[str, str]]) -> str:
    boundary_lines = []
    for patch_name, entry in boundary_entries.items():
        lines = [f"        type            {entry['type']};"]
        if "value" in entry:
            lines.append(f"        value           {entry['value']};")
        boundary_lines.append(
            f"    {patch_name}\n"
            "    {\n"
            + "\n".join(lines)
            + "\n"
            "    }"
        )
    return (
        f"{_foam_header('volVectorField' if name == 'U' else 'volScalarField', name)}\n"
        f"dimensions      {dimensions};\n\n"
        f"internalField   {internal_field};\n\n"
        "boundaryField\n"
        "{\n"
        + "\n".join(boundary_lines)
        + "\n}\n"
    )


def _write_potentialfoam_case(config: dict[str, Any], output_dir: Path) -> list[str]:
    solve = config["downstream_solve"]
    velocity = _foam_vector(solve["fields"]["inlet_velocity_m_s"])
    pressure = float(solve["fields"]["initial_pressure_m2_s2"])
    control = solve["control"]
    numerics = solve["numerics"]

    u_boundaries: dict[str, dict[str, str]] = {}
    p_boundaries: dict[str, dict[str, str]] = {}
    for patch_name, role in _physical_surface_roles(config):
        if role == "inlet":
            u_boundaries[patch_name] = {"type": "fixedValue", "value": f"uniform {velocity}"}
            p_boundaries[patch_name] = {"type": "zeroGradient"}
        elif role == "outlet":
            u_boundaries[patch_name] = {"type": "zeroGradient"}
            p_boundaries[patch_name] = {"type": "fixedValue", "value": "uniform 0"}
        else:
            u_boundaries[patch_name] = {"type": "fixedValue", "value": "uniform (0 0 0)"}
            p_boundaries[patch_name] = {"type": "zeroGradient"}

    files = {
        "0/U": _field_file("U", "[0 1 -1 0 0 0 0]", f"uniform {velocity}", u_boundaries),
        "0/p": _field_file("p", "[0 2 -2 0 0 0 0]", f"uniform {pressure:g}", p_boundaries),
        "system/controlDict": (
            f"{_foam_header('dictionary', 'controlDict')}\n"
            f"application     {solve['application']};\n\n"
            "startFrom       startTime;\n"
            f"startTime       {float(control['start_time']):g};\n\n"
            "stopAt          endTime;\n"
            f"endTime         {float(control['end_time']):g};\n\n"
            f"deltaT          {float(control['delta_t']):g};\n\n"
            "writeControl    timeStep;\n"
            f"writeInterval   {int(control['write_interval'])};\n"
            "purgeWrite      0;\n"
            "writeFormat     ascii;\n"
            "writePrecision  6;\n"
            "writeCompression off;\n"
            "timeFormat      general;\n"
            "timePrecision   6;\n"
            "runTimeModifiable true;\n"
        ),
        "system/fvSchemes": (
            f"{_foam_header('dictionary', 'fvSchemes')}\n"
            "ddtSchemes\n"
            "{\n"
            "    default         steadyState;\n"
            "}\n\n"
            "gradSchemes\n"
            "{\n"
            "    default         Gauss linear;\n"
            "}\n\n"
            "divSchemes\n"
            "{\n"
            "    default         none;\n"
            f"    div(phi,U)      {numerics['div_phi_U']};\n"
            f"    div(div(phi,U)) {numerics['div_div_phi_U']};\n"
            "}\n\n"
            "laplacianSchemes\n"
            "{\n"
            f"    default         {numerics['laplacian_default']};\n"
            "}\n\n"
            "interpolationSchemes\n"
            "{\n"
            "    default         linear;\n"
            "}\n\n"
            "snGradSchemes\n"
            "{\n"
            "    default         corrected;\n"
            "}\n"
        ),
        "system/fvSolution": (
            f"{_foam_header('dictionary', 'fvSolution')}\n"
            "solvers\n"
            "{\n"
            "    Phi\n"
            "    {\n"
            "        solver          GAMG;\n"
            "        smoother        DIC;\n"
            "        tolerance       1e-08;\n"
            "        relTol          0.01;\n"
            "    }\n"
            "    p\n"
            "    {\n"
            "        $Phi;\n"
            "    }\n"
            "}\n\n"
            "potentialFlow\n"
            "{\n"
            f"    nNonOrthogonalCorrectors {int(numerics['n_non_orthogonal_correctors'])};\n"
            "}\n"
        ),
    }
    written: list[str] = []
    for rel_path, text in files.items():
        path = output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(rel_path)
    return written


def _fatal_error_detected(log_text: str) -> bool:
    return "FOAM FATAL" in log_text or re.search(r"(?mi)^(?!trapFpe:).*Floating point exception", log_text) is not None


def _parse_potentialfoam_logs(check_mesh_log: str, solver_log: str) -> dict[str, Any]:
    final_residuals = [
        float(match.group(1))
        for match in re.finditer(r"Final residual = ([0-9.eE+-]+)", solver_log)
    ]
    continuity_errors = [
        abs(float(match.group(1)))
        for match in re.finditer(r"Continuity error\s*=\s*([0-9.eE+-]+)", solver_log)
    ]
    interpolated_velocity_errors = [
        abs(float(match.group(1)))
        for match in re.finditer(r"Interpolated velocity error\s*=\s*([0-9.eE+-]+)", solver_log)
    ]
    fatal = _fatal_error_detected(check_mesh_log) or _fatal_error_detected(solver_log)
    return {
        "check_mesh_ok": "Mesh OK" in check_mesh_log,
        "potentialFoam_completed": re.search(r"^End\s*$", solver_log, flags=re.MULTILINE) is not None,
        "max_final_residual": max(final_residuals) if final_residuals else None,
        "final_residual_count": len(final_residuals),
        "max_continuity_error": max(continuity_errors) if continuity_errors else None,
        "continuity_error_count": len(continuity_errors),
        "max_interpolated_velocity_error": max(interpolated_velocity_errors) if interpolated_velocity_errors else None,
        "interpolated_velocity_error_count": len(interpolated_velocity_errors),
        "fatal_error_detected": fatal,
    }


def summarize_solve_outputs(output_dir: Path, expected_outputs: list[str]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for rel_path in expected_outputs:
        path = output_dir / rel_path
        files[rel_path] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
    return {"files": files}


def summarize_openfoam_polymesh(output_dir: Path, expected_outputs: list[str]) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for rel_path in expected_outputs:
        path = output_dir / rel_path
        files[rel_path] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    poly_mesh = output_dir / "constant" / "polyMesh"
    counts = {}
    for name in ["points", "faces", "owner", "neighbour"]:
        path = poly_mesh / name
        counts[name] = _foam_list_count(path) if path.exists() else None

    boundary_path = poly_mesh / "boundary"
    boundary_names = _parse_boundary_names(boundary_path) if boundary_path.exists() else []
    return {
        "files": files,
        "counts": counts,
        "boundary_names": boundary_names,
        "structural_checks": {
            "has_points": isinstance(counts.get("points"), int) and counts["points"] > 0,
            "has_faces": isinstance(counts.get("faces"), int) and counts["faces"] > 0,
            "owner_matches_faces": counts.get("owner") == counts.get("faces") and isinstance(counts.get("faces"), int),
            "neighbour_not_larger_than_faces": (
                isinstance(counts.get("neighbour"), int)
                and isinstance(counts.get("faces"), int)
                and counts["neighbour"] <= counts["faces"]
            ),
        },
    }


def _write_openfoam_control_dict(output_dir: Path) -> Path:
    system_dir = output_dir / "system"
    system_dir.mkdir(parents=True, exist_ok=True)
    control_dict = system_dir / "controlDict"
    control_dict.write_text(
        "\n".join(
            [
                "FoamFile",
                "{",
                "    version     2.0;",
                "    format      ascii;",
                "    class       dictionary;",
                "    object      controlDict;",
                "}",
                "application     gmshToFoam;",
                "startFrom       startTime;",
                "startTime       0;",
                "stopAt          endTime;",
                "endTime         0;",
                "deltaT          1;",
                "writeControl    timeStep;",
                "writeInterval   1;",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "constant").mkdir(parents=True, exist_ok=True)
    return control_dict


def run_downstream_import(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    downstream = config.get("downstream_import") or {}
    if not downstream.get("enabled"):
        return {"enabled": False, "status": "not_configured"}

    poly_mesh_dir = output_dir / "constant" / "polyMesh"
    if poly_mesh_dir.exists():
        shutil.rmtree(poly_mesh_dir)
    _write_openfoam_control_dict(output_dir)

    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "log.gmshToFoam"
    timeout_s = float(downstream["timeout_s"])
    distro = downstream["wsl_distro"]
    bashrc_path = downstream["bashrc_path"]
    case_dir_linux = map_windows_path_to_wsl(output_dir, distro, timeout_s)
    command = downstream["command"]
    script = (
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
        f"cd {shlex.quote(case_dir_linux)}; "
        "command -v gmshToFoam >/dev/null 2>&1 || exit 127; "
        f"{command}"
    )
    result = run_wsl(distro, script, timeout_s)
    log_text = result.stdout
    if result.stderr:
        log_text += result.stderr
    log_path.write_text(log_text, encoding="utf-8")

    expected_outputs = list(downstream["expected_outputs"])
    poly_summary = summarize_openfoam_polymesh(output_dir, expected_outputs)
    expected_present = all(
        rel_path == "downstream_import_summary.json" or (item["exists"] and item["size_bytes"] > 0)
        for rel_path, item in poly_summary["files"].items()
    )
    required_boundaries = set(downstream["expected_boundary_names"])
    boundary_names = set(poly_summary["boundary_names"])
    structural_passed = all(poly_summary["structural_checks"].values())
    status = "passed" if result.returncode == 0 and expected_present and required_boundaries.issubset(boundary_names) and structural_passed else "failed"
    summary = {
        "enabled": True,
        "status": status,
        "engine": downstream["engine"],
        "runtime_profile": downstream["runtime_profile"],
        "command": command,
        "returncode": result.returncode,
        "log": str(log_path),
        "required_boundary_names": sorted(required_boundaries),
        "polyMesh": poly_summary,
    }
    summary_path = output_dir / "downstream_import_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if "downstream_import_summary.json" in summary["polyMesh"]["files"]:
        summary["polyMesh"]["files"]["downstream_import_summary.json"] = {
            "path": str(summary_path),
            "exists": True,
            "size_bytes": summary_path.stat().st_size,
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_downstream_solve(config: dict[str, Any], output_dir: Path, import_summary: dict[str, Any]) -> dict[str, Any]:
    solve = config.get("downstream_solve") or {}
    if not solve.get("enabled"):
        return {"enabled": False, "status": "not_configured"}
    if import_summary.get("status") != "passed":
        summary = {
            "enabled": True,
            "status": "failed",
            "engine": solve["engine"],
            "runtime_profile": solve["runtime_profile"],
            "precondition": "downstream_import.status == passed",
            "import_status": import_summary.get("status", "not_configured"),
        }
        summary_path = output_dir / "downstream_solve_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    written_case_files = _write_potentialfoam_case(config, output_dir)
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timeout_s = float(solve["timeout_s"])
    distro = solve["wsl_distro"]
    bashrc_path = solve["bashrc_path"]
    case_dir_linux = map_windows_path_to_wsl(output_dir, distro, timeout_s)
    command_results: list[dict[str, Any]] = []
    logs_by_executable: dict[str, str] = {}
    for command in solve["command_sequence"]:
        executable = shlex.split(command)[0]
        log_path = logs_dir / f"log.{Path(executable).name}"
        script = (
            f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
            f"cd {shlex.quote(case_dir_linux)}; "
            f"command -v {shlex.quote(executable)} >/dev/null 2>&1 || exit 127; "
            f"{command}"
        )
        result = run_wsl(distro, script, timeout_s)
        log_text = result.stdout
        if result.stderr:
            log_text += result.stderr
        log_path.write_text(log_text, encoding="utf-8")
        logs_by_executable[Path(executable).name] = log_text
        command_results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "log": str(log_path),
            }
        )
        if result.returncode != 0:
            break

    log_metrics = _parse_potentialfoam_logs(
        logs_by_executable.get("checkMesh", ""),
        logs_by_executable.get("potentialFoam", ""),
    )
    expected_outputs = list(solve["expected_outputs"])
    file_summary = summarize_solve_outputs(output_dir, expected_outputs)
    expected_present = all(
        rel_path == "downstream_solve_summary.json" or (item["exists"] and item["size_bytes"] > 0)
        for rel_path, item in file_summary["files"].items()
    )
    validation = solve["validation"]
    required_boundaries = set(validation["required_boundary_names"])
    boundary_names = set(import_summary.get("polyMesh", {}).get("boundary_names", []))
    continuity_error = log_metrics["max_continuity_error"]
    solve_passed = (
        all(item["returncode"] == 0 for item in command_results)
        and expected_present
        and required_boundaries.issubset(boundary_names)
        and (not validation["require_check_mesh_ok"] or log_metrics["check_mesh_ok"])
        and log_metrics["potentialFoam_completed"]
        and continuity_error is not None
        and continuity_error <= float(validation["max_continuity_error"])
        and not log_metrics["fatal_error_detected"]
    )
    summary = {
        "enabled": True,
        "status": "passed" if solve_passed else "failed",
        "engine": solve["engine"],
        "runtime_profile": solve["runtime_profile"],
        "application": solve["application"],
        "command_sequence": solve["command_sequence"],
        "command_results": command_results,
        "written_case_files": written_case_files,
        "required_boundary_names": sorted(required_boundaries),
        "boundary_names": sorted(boundary_names),
        **log_metrics,
        **file_summary,
    }
    summary_path = output_dir / "downstream_solve_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if "downstream_solve_summary.json" in summary["files"]:
        summary["files"]["downstream_solve_summary.json"] = {
            "path": str(summary_path),
            "exists": True,
            "size_bytes": summary_path.stat().st_size,
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def generate_mesh(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    gmsh = _import_gmsh()
    geo_path = output_dir / "case.geo"
    mesh_path = output_dir / "case.msh"
    gmsh.initialize()
    try:
        gmsh.open(str(geo_path))
        gmsh.option.setNumber("Mesh.ElementOrder", int(config["mesh"]["element_order"]))
        gmsh.option.setNumber("Mesh.Algorithm", int(config["mesh"]["algorithm"]))
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2 if config["mesh"]["output_format"] == "msh2" else 4.1)
        dimension = int(config["mesh"]["dimension"])
        gmsh.model.mesh.generate(dimension)
        gmsh.write(str(mesh_path))
        summary = _summarize_mesh(gmsh, dimension)
    finally:
        gmsh.finalize()

    summary["artifacts"] = {
        "case.geo": str(geo_path),
        "case.msh": str(mesh_path),
        "mesh_summary.json": str(output_dir / "mesh_summary.json"),
        "downstream_import_summary.json": str(output_dir / "downstream_import_summary.json"),
        "downstream_solve_summary.json": str(output_dir / "downstream_solve_summary.json"),
        "validation.json": str(output_dir / "validation.json"),
        "validation_report.md": str(output_dir / "validation_report.md"),
    }
    downstream_summary = run_downstream_import(config, output_dir)
    if downstream_summary.get("enabled"):
        summary["downstream_import"] = downstream_summary
    solve_summary = run_downstream_solve(config, output_dir, downstream_summary)
    if solve_summary.get("enabled"):
        summary["downstream_solve"] = solve_summary
    summary_path = output_dir / "mesh_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    validation = validate_mesh_summary(summary, config, output_dir)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_dir / "validation_report.md", config, summary, validation)
    return {"summary": summary, "validation": validation}
