"""Runner for Fluent C02 verification reference mapping."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import (
    summarize_mesh_runtime_metrics,
    summarize_reference_metrics,
    validate_pressure_solve_smoke,
    validate_manifest,
    validate_mesh_runtime_smoke,
)

SCHEMA_ID = "schemas/fluent_C02_verification_reference_validation.schema.json"
AXIS_FACE_ZONE_TYPE = 0x25


def _reference_manifest(config: dict[str, Any]) -> dict[str, Any]:
    manifest = {
        "reference_source": config["reference_source"],
        "governing_model": config["governing_model"],
        "geometry": config["geometry"],
        "material_properties": config["material_properties"],
        "boundary_conditions": config["boundary_conditions"],
        "reference_formula": config["reference_formula"],
        "reference_values": config["reference_values"],
        "sampling_policy": config["sampling_policy"],
        "validation_targets": {
            "max_manual_relative_error": config["validation"]["max_manual_relative_error"],
        },
        "scope": "verification-manual reference mapping",
    }
    if "mesh_generation" in config:
        manifest["mesh_generation"] = config["mesh_generation"]
    if "runtime_smoke" in config:
        manifest["runtime_smoke"] = config["runtime_smoke"]
    if "solver_setup" in config:
        manifest["solver_setup"] = config["solver_setup"]
    return manifest


def _write_reference_artifacts(output_dir: Path, config: dict[str, Any]) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reference_manifest.json").write_text(
        json.dumps(_reference_manifest(config), indent=2),
        encoding="utf-8",
    )
    return ["reference_manifest.json"]


def _to_fluent_path(path: Path) -> str:
    return path.resolve().as_posix()


def _env_path(env_name: str, label: str) -> Path:
    value = os.environ.get(env_name)
    if not value:
        raise ValueError(f"Missing required environment variable {env_name} for {label}.")
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"{label} path from {env_name} does not exist: {path}")
    return path


def _node_id(radial_points: int, axial_index: int, radial_index: int) -> int:
    return axial_index * radial_points + radial_index + 1


def _cell_id(radial_cells: int, axial_index: int, radial_index: int) -> int:
    return axial_index * radial_cells + radial_index + 1


def _format_face(first_node: int, second_node: int, left_cell: int, right_cell: int) -> str:
    return f"{first_node:x} {second_node:x} {left_cell:x} {right_cell:x}"


def _pipe_mesh_lines(config: dict[str, Any]) -> list[str]:
    mesh = config["mesh_generation"]
    length = float(config["geometry"]["length_m"])
    radius = float(config["geometry"]["radius_m"])
    axial_cells = int(mesh["axial_cells"])
    radial_cells = int(mesh["radial_cells"])
    radial_points = radial_cells + 1
    node_count = (axial_cells + 1) * radial_points

    lines = [
        '(0 "Generated VMFL005 axisymmetric pipe mesh")',
        "(2 2)",
        f"(10 (0 1 {node_count:x} 0 2))",
        f"(10 (1 1 {node_count:x} 1 2)(",
    ]
    for axial_index in range(axial_cells + 1):
        x_coord = length * axial_index / axial_cells
        for radial_index in range(radial_points):
            y_coord = radius * radial_index / radial_cells
            lines.append(f"{x_coord:.12e} {y_coord:.12e}")
    lines.append("))")

    interior_faces: list[str] = []
    inlet_faces: list[str] = []
    outlet_faces: list[str] = []
    axis_faces: list[str] = []
    wall_faces: list[str] = []

    for axial_index in range(axial_cells + 1):
        for radial_index in range(radial_cells):
            if axial_index == 0:
                inlet_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index, radial_index + 1),
                        _node_id(radial_points, axial_index, radial_index),
                        _cell_id(radial_cells, 0, radial_index),
                        0,
                    )
                )
            elif axial_index == axial_cells:
                outlet_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index, radial_index),
                        _node_id(radial_points, axial_index, radial_index + 1),
                        _cell_id(radial_cells, axial_cells - 1, radial_index),
                        0,
                    )
                )
            else:
                interior_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index, radial_index),
                        _node_id(radial_points, axial_index, radial_index + 1),
                        _cell_id(radial_cells, axial_index - 1, radial_index),
                        _cell_id(radial_cells, axial_index, radial_index),
                    )
                )

    for axial_index in range(axial_cells):
        for radial_index in range(radial_points):
            if radial_index == 0:
                axis_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index, radial_index),
                        _node_id(radial_points, axial_index + 1, radial_index),
                        _cell_id(radial_cells, axial_index, 0),
                        0,
                    )
                )
            elif radial_index == radial_cells:
                wall_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index + 1, radial_index),
                        _node_id(radial_points, axial_index, radial_index),
                        _cell_id(radial_cells, axial_index, radial_cells - 1),
                        0,
                    )
                )
            else:
                interior_faces.append(
                    _format_face(
                        _node_id(radial_points, axial_index, radial_index),
                        _node_id(radial_points, axial_index + 1, radial_index),
                        _cell_id(radial_cells, axial_index, radial_index),
                        _cell_id(radial_cells, axial_index, radial_index - 1),
                    )
                )

    zones = mesh["zone_names"]
    sections = [
        {"id": 2, "type": 2, "kind": "interior", "name": zones["interior"], "faces": interior_faces},
        {"id": 3, "type": 3, "kind": "wall", "name": zones["wall"], "faces": wall_faces},
        {"id": 4, "type": AXIS_FACE_ZONE_TYPE, "kind": "axis", "name": zones["axis"], "faces": axis_faces},
        {"id": 5, "type": 5, "kind": "pressure-outlet", "name": zones["outlet"], "faces": outlet_faces},
        {"id": 6, "type": 10, "kind": "velocity-inlet", "name": zones["inlet"], "faces": inlet_faces},
    ]
    total_faces = sum(len(section["faces"]) for section in sections)
    lines.append(f"(13 (0 1 {total_faces:x} 0))")
    face_id = 1
    for section in sections:
        faces = section["faces"]
        first_face = face_id
        last_face = face_id + len(faces) - 1
        lines.append(f"(13 ({section['id']:x} {first_face:x} {last_face:x} {section['type']:x} 2) (")
        lines.extend(faces)
        lines.append("))")
        face_id = last_face + 1

    cell_count = axial_cells * radial_cells
    lines.extend(
        [
            f"(12 (0 1 {cell_count:x} 0))",
            f"(12 (1 1 {cell_count:x} 1 3))",
            '(0 "Zones:")',
            f"(45 (1 fluid {zones['fluid']})())",
        ]
    )
    for section in sections:
        lines.append(f"(45 ({section['id']:x} {section['kind']} {section['name']})())")
    return lines


def _write_pipe_mesh(output_dir: Path, config: dict[str, Any]) -> Path:
    mesh_path = output_dir / config["mesh_generation"]["mesh_file"]
    mesh_path.write_text("\n".join(_pipe_mesh_lines(config)) + "\n", encoding="ascii")
    return mesh_path


def _write_mesh_manifest(output_dir: Path, config: dict[str, Any], mesh_path: Path) -> None:
    mesh = config["mesh_generation"]
    mesh_manifest = {
        "mesh_file": mesh_path.name,
        "domain": "2D axisymmetric half-domain pipe mesh",
        "length_m": config["geometry"]["length_m"],
        "radius_m": config["geometry"]["radius_m"],
        "axial_cells": mesh["axial_cells"],
        "radial_cells": mesh["radial_cells"],
        "cell_count": mesh["axial_cells"] * mesh["radial_cells"],
        "zone_names": mesh["zone_names"],
        "axis_face_zone_type": "axis",
        "orientation_policy": "face left-cell/right-cell ordering follows Fluent mesh import convention",
    }
    (output_dir / "mesh_manifest.json").write_text(json.dumps(mesh_manifest, indent=2), encoding="utf-8")


def _material_setup_lines(config: dict[str, Any]) -> list[str]:
    material = config["material_properties"]
    return [
        "/define/materials/change-create air air",
        "yes",
        "constant",
        f"{material['density_kg_m3']}",
        "no",
        "no",
        "yes",
        "constant",
        f"{material['dynamic_viscosity_kg_m_s']}",
        "no",
        "no",
        "no",
    ]


def _velocity_inlet_lines(config: dict[str, Any]) -> list[str]:
    velocity = config["boundary_conditions"]["inlet_average_velocity_m_s"]
    return [
        "/define/boundary-conditions/velocity-inlet inlet",
        "yes",
        "yes",
        "no",
        f"{velocity}",
        "no",
        "0",
        "no",
        "1",
        "no",
        "0",
    ]


def _pressure_solve_lines(config: dict[str, Any]) -> list[str]:
    setup = config["solver_setup"]
    return [
        "/define/models/axisymmetric yes",
        "/define/models/viscous/laminar yes",
        *_material_setup_lines(config),
        *_velocity_inlet_lines(config),
        "/mesh/check",
        "/solve/initialize/hyb-initialization",
        f"/solve/iterate {setup['max_iterations']}",
        *_pressure_report_lines(),
    ]


def _pressure_report_lines() -> list[str]:
    lines = []
    for zone_name in ["inlet", "outlet"]:
        lines.extend(
            [
                "/report/surface-integrals/area-weighted-avg",
                zone_name,
                "()",
                "pressure",
                "no",
            ]
        )
    return lines


def _journal_text(config: dict[str, Any], mesh_path: Path, resolved_paths: bool) -> str:
    mesh_text = _to_fluent_path(mesh_path) if resolved_paths else mesh_path.as_posix()
    lines = [
        f'/file/read-case "{mesh_text}"',
    ]
    if config["backend"]["type"] == "fluent_pressure_solve_smoke":
        lines.extend(_pressure_solve_lines(config))
    else:
        lines.append("/mesh/check")
    if config["runtime_smoke"]["write_case"]:
        case_path = mesh_path.parent / config["runtime_smoke"]["case_file"]
        case_text = _to_fluent_path(case_path) if resolved_paths else case_path.as_posix()
        lines.append(f'/file/write-case "{case_text}"')
    lines.append("/exit yes")
    return "\n".join(lines) + "\n"


def _write_journal(config: dict[str, Any], output_dir: Path, mesh_path: Path, resolved_paths: bool) -> Path:
    journal_path = output_dir / config["runtime_smoke"]["journal_file"]
    journal_path.write_text(_journal_text(config, mesh_path, resolved_paths), encoding="ascii")
    return journal_path


def _write_dry_run_runtime_placeholders(output_dir: Path) -> list[str]:
    placeholder_text = "dry-run placeholder; Fluent was not executed for this artifact.\n"
    written = []
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        (output_dir / name).write_text(placeholder_text, encoding="utf-8")
        written.append(name)
    return written


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str]) -> dict[str, Any]:
    reference_manifest = _reference_manifest(config)
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(output_dir),
        "fluent": config["fluent"],
        "backend": config["backend"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "runtime_commands": [
            "static-contract:build reference_manifest.json"
            if config["backend"]["type"] == "dry_run_only"
            else "fluent 2ddp -g -tN -i journal.jou",
            "static-contract:validate manual target table"
            if config["backend"]["type"] == "dry_run_only"
            else "runtime-smoke:read self-generated mesh and run mesh/check",
        ],
        "scope": "Fluent C02 verification reference static-readiness"
        if config["backend"]["type"] == "dry_run_only"
        else (
            "Fluent C02 self-generated VMFL005 axisymmetric solve smoke"
            if config["backend"]["type"] == "fluent_pressure_solve_smoke"
            else "Fluent C02 self-generated VMFL005 mesh runtime smoke"
        ),
        **reference_manifest,
    }


def _collect_root_fluent_artifacts(before: set[Path], output_dir: Path) -> None:
    after = set(REPO_ROOT.glob("fluent-*.trn")) | set(REPO_ROOT.glob("cleanup-fluent-*.bat"))
    for path in sorted(after - before):
        target = output_dir / path.name
        shutil.move(str(path), str(target))
        if path.suffix.lower() == ".trn":
            shutil.copyfile(target, output_dir / "transcript.txt")


def _execute_fluent(config: dict[str, Any], output_dir: Path, journal_path: Path) -> int:
    fluent_exe = _env_path(config["fluent"]["executable_env"], "Fluent executable")
    args = [
        str(fluent_exe),
        config["fluent"]["dimension_precision"],
        *config["fluent"]["headless_flags"],
        f"-t{config['fluent']['processor_count']}",
        config["fluent"]["journal_argument"],
        str(journal_path),
    ]
    before = set(REPO_ROOT.glob("fluent-*.trn")) | set(REPO_ROOT.glob("cleanup-fluent-*.bat"))
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, stderr_path.open(
        "w", encoding="utf-8", errors="replace"
    ) as stderr:
        result = subprocess.run(
            args,
            cwd=REPO_ROOT,
            stdout=stdout,
            stderr=stderr,
            timeout=float(config["backend"]["timeout_s"]),
            check=False,
        )
    _collect_root_fluent_artifacts(before, output_dir)
    if not (output_dir / "transcript.txt").exists():
        shutil.copyfile(stdout_path, output_dir / "transcript.txt")
    return result.returncode


def _runtime_text(output_dir: Path) -> str:
    parts = []
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        path = output_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _first_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if match is None:
        return None
    return float(match.group(1))


def _pressure_report_value(text: str, zone_name: str) -> float | None:
    pattern = (
        r"Area-Weighted Average\s+"
        r"Static Pressure\s+\[Pa\]\s+"
        r"[-\s]+\s*"
        rf"{re.escape(zone_name)}\s+([-+0-9.eE]+)"
    )
    return _first_float(pattern, text)


def _collect_runtime_metrics(config: dict[str, Any], output_dir: Path, return_code: int) -> dict[str, Any]:
    text = _runtime_text(output_dir)
    face_counts: dict[str, int] = {}
    for match in re.finditer(r"\s+(\d+)\s+2D\s+([A-Za-z-]+)\s+faces,\s+zone\s+\d+", text):
        face_counts[match.group(2)] = face_counts.get(match.group(2), 0) + int(match.group(1))
    cell_match = re.search(r"\s+(\d+)\s+quadrilateral\s+cells,\s+zone\s+\d+", text)
    mesh = config["mesh_generation"]
    expected_cells = mesh["axial_cells"] * mesh["radial_cells"]
    metrics = {
        "fluent_return_code": return_code,
        "mesh_node_count": (mesh["axial_cells"] + 1) * (mesh["radial_cells"] + 1),
        "mesh_cell_count": int(cell_match.group(1)) if cell_match else None,
        "expected_mesh_cell_count": expected_cells,
        "mesh_face_counts": face_counts,
        "mesh_check_completed": "Checking mesh" in text and "Done." in text,
        "minimum_cell_volume_m3": _first_float(r"minimum volume \(m3\):\s+([0-9.eE+-]+)", text),
        "maximum_cell_volume_m3": _first_float(r"maximum volume \(m3\):\s+([0-9.eE+-]+)", text),
        "total_cell_volume_m3": _first_float(r"total volume \(m3\):\s+([0-9.eE+-]+)", text),
        "fluent_warning_count": text.count("Warning:"),
        "fluent_error_count": text.count("Error:"),
        "axis_boundary_warning_detected": "axis boundary conditions is not appropriate" in text,
        "pressure_drop_runtime_status": "not_extracted_in_mesh_smoke",
        "runtime_scope": "mesh-readability and mesh/check only; no pressure-drop solve",
    }
    if config["backend"]["type"] == "fluent_pressure_solve_smoke":
        residual_rows = [
            {
                "iteration": int(match.group(1)),
                "continuity": float(match.group(2)),
                "x_velocity": float(match.group(3)),
                "y_velocity": float(match.group(4)),
            }
            for match in re.finditer(
                r"^\s*(\d+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+",
                text,
                re.MULTILINE,
            )
        ]
        final_residuals = residual_rows[-1] if residual_rows else {}
        inlet_pressure = _pressure_report_value(text, "inlet")
        outlet_pressure = _pressure_report_value(text, "outlet")
        pressure_drop = None
        pressure_drop_relative_error = None
        if inlet_pressure is not None and outlet_pressure is not None:
            pressure_drop = inlet_pressure - outlet_pressure
            target = float(config["reference_values"]["target_pressure_drop_pa"])
            pressure_drop_relative_error = abs(pressure_drop - target) / target
        metrics.update(
            {
                "solution_converged": "solution is converged" in text,
                "iteration_count": int(final_residuals["iteration"]) if final_residuals else None,
                "final_residuals": final_residuals,
                "inlet_area_weighted_static_pressure_pa": inlet_pressure,
                "outlet_area_weighted_static_pressure_pa": outlet_pressure,
                "runtime_pressure_drop_pa": pressure_drop,
                "pressure_drop_relative_error": pressure_drop_relative_error,
                "pressure_drop_runtime_status": "surface_integral_area_weighted_pressure_sampled"
                if pressure_drop is not None
                else "surface_integral_pressure_report_missing",
                "runtime_scope": (
                    "axisymmetric laminar pressure-solve smoke with inlet/outlet area-weighted pressure sampling; "
                    "uniform inlet profile remains a tracked VMFL005 homology gap"
                ),
            }
        )
    return metrics


def run(
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
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
    backend_type = config["backend"]["type"]
    if not dry_run and backend_type == "dry_run_only":
        raise ValueError("Fluent C02 dry_run_only backend requires dry_run=True.")
    if backend_type not in {"dry_run_only", "fluent_mesh_check", "fluent_pressure_solve_smoke"}:
        raise NotImplementedError(f"Fluent C02 backend {config['backend']['type']!r} is not implemented.")

    resolved_output_dir = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = _write_reference_artifacts(resolved_output_dir, config)

    if backend_type in {"fluent_mesh_check", "fluent_pressure_solve_smoke"}:
        mesh_path = _write_pipe_mesh(resolved_output_dir, config)
        _write_mesh_manifest(resolved_output_dir, config, mesh_path)
        journal_path = _write_journal(config, resolved_output_dir, mesh_path, resolved_paths=not dry_run)
        generated_files.extend([mesh_path.name, "mesh_manifest.json", journal_path.name])
        if dry_run:
            generated_files.extend(_write_dry_run_runtime_placeholders(resolved_output_dir))

    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = _build_manifest(config, resolved_output_dir, generated_files)
    if dry_run or backend_type == "dry_run_only":
        validation = validate_manifest(manifest, config)
        metrics = summarize_reference_metrics(config, validation)
        manifest["validation"] = validation
        manifest["metrics"] = metrics
        (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
        (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        validation = validate_manifest(manifest, config, resolved_output_dir)
        metrics = summarize_reference_metrics(config, validation)
        manifest["validation"] = validation
        manifest["metrics"] = metrics
        (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
        (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
        (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    journal_path = resolved_output_dir / config["runtime_smoke"]["journal_file"]
    return_code = _execute_fluent(config, resolved_output_dir, journal_path)
    generated_files.extend(["stdout.txt", "stderr.txt", "transcript.txt"])
    manifest["generated_files"] = generated_files
    runtime_metrics = _collect_runtime_metrics(config, resolved_output_dir, return_code)
    metrics = summarize_mesh_runtime_metrics(config, runtime_metrics)
    if backend_type == "fluent_pressure_solve_smoke":
        validation = validate_pressure_solve_smoke(manifest, config, metrics, resolved_output_dir, check_artifacts=False)
    else:
        validation = validate_mesh_runtime_smoke(manifest, config, metrics, resolved_output_dir, check_artifacts=False)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (resolved_output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if backend_type == "fluent_pressure_solve_smoke":
        validation = validate_pressure_solve_smoke(manifest, config, metrics, resolved_output_dir, check_artifacts=True)
    else:
        validation = validate_mesh_runtime_smoke(manifest, config, metrics, resolved_output_dir, check_artifacts=True)
    manifest["validation"] = validation
    (resolved_output_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(resolved_output_dir / "validation_report.md", config, metrics, validation)
    (resolved_output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
