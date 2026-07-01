"""OpenFOAM runtime execution and log parsing for C04."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.template_case import execute_command_sequence

from .postprocess import read_y_plus_log, write_force_metrics, write_y_plus_summary
from .validation import validate_runtime_metrics

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
RESIDUAL_RE = re.compile(
    rf"(?:\w+:\s+)?Solving for\s+(?P<field>[\w.]+),\s+Initial residual =\s*(?P<initial>{FLOAT_RE}),\s+"
    rf"Final residual =\s*(?P<final>{FLOAT_RE}),\s+No Iterations\s+(?P<iterations>\d+)"
)
CELL_COUNT_RE = re.compile(r"cells:\s+(\d+)")
NON_ORTHO_RE = re.compile(rf"(?:Max\s+non-orthogonality\s+=|Mesh\s+non-orthogonality\s+Max:)\s*({FLOAT_RE})")
ASPECT_RE = re.compile(rf"Max\s+aspect\s+ratio\s+=\s+({FLOAT_RE})")
SKEW_RE = re.compile(rf"Max\s+skewness\s+=\s+({FLOAT_RE})")
HIGHLY_SKEW_RE = re.compile(r"(\d+)\s+highly skew faces", re.IGNORECASE)


def _true_floating_exception(log_text: str) -> bool:
    return any("Floating point exception" in line and "trapping enabled" not in line for line in log_text.splitlines())


def parse_simplefoam_log(log_text: str) -> dict[str, Any]:
    residual_history = []
    for match in RESIDUAL_RE.finditer(log_text):
        residual_history.append(
            {
                "field": match.group("field"),
                "initial": float(match.group("initial")),
                "final": float(match.group("final")),
                "iterations": int(match.group("iterations")),
            }
        )
    max_final = max((item["final"] for item in residual_history), default=math.nan)
    fatal = "FOAM FATAL" in log_text or "FOAM exiting" in log_text or "Segmentation fault" in log_text or _true_floating_exception(log_text)
    return {
        "started": "Starting time loop" in log_text or bool(residual_history),
        "fatal_error_detected": fatal,
        "residual_history": residual_history,
        "max_final_residual": max_final,
    }


def parse_mesh_logs(snappy_log: str, check_mesh_log: str) -> dict[str, Any]:
    cell_match = CELL_COUNT_RE.search(check_mesh_log)
    non_ortho_match = NON_ORTHO_RE.search(check_mesh_log)
    aspect_match = ASPECT_RE.search(check_mesh_log)
    skew_match = SKEW_RE.search(check_mesh_log)
    highly_skew_match = HIGHLY_SKEW_RE.search(check_mesh_log)
    return {
        "snappy_completed": "Finished meshing" in snappy_log or "End" in snappy_log,
        "mesh_ok": "Mesh OK" in check_mesh_log,
        "fatal_error_detected": "FOAM FATAL" in check_mesh_log or "Failed" in check_mesh_log,
        "cell_count": int(cell_match.group(1)) if cell_match else 0,
        "max_non_orthogonality": float(non_ortho_match.group(1)) if non_ortho_match else math.nan,
        "max_aspect_ratio": float(aspect_match.group(1)) if aspect_match else math.nan,
        "max_skewness": float(skew_match.group(1)) if skew_match else math.nan,
        "highly_skew_face_count": int(highly_skew_match.group(1)) if highly_skew_match else 0,
    }


def execute_wsl_runtime(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return execute_command_sequence(config, output_dir)


def _command_log(runtime: dict[str, Any], token: str, output_dir: Path) -> Path:
    for item in runtime.get("commands", []):
        if token in item.get("command", ""):
            return Path(item["log"])
    return output_dir / "logs" / f"log.{token}"


def _read_face_set_count(path: Path) -> int | None:
    if not path.exists():
        return None
    return len(_read_label_list(path))


def _read_foam_list_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        inline_match = re.match(r"^(\d+)\s*\((.*)\)$", stripped)
        if inline_match:
            inner = inline_match.group(2).strip()
            return [inner] if inner else []
        if not stripped.isdigit():
            continue
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index >= len(lines) or lines[next_index].strip() != "(":
            continue
        body: list[str] = []
        for body_line in lines[next_index + 1:]:
            if body_line.strip() == ")":
                break
            if body_line.strip():
                body.append(body_line.strip())
        return body
    return []


def _read_label_list(path: Path) -> list[int]:
    labels: list[int] = []
    for line in _read_foam_list_lines(path):
        labels.extend(int(value) for value in re.findall(r"\d+", line))
    return labels


def _read_points(path: Path) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for line in _read_foam_list_lines(path):
        match = re.match(rf"^\(\s*({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*\)$", line)
        if match:
            points.append((float(match.group(1)), float(match.group(2)), float(match.group(3))))
    return points


def _face_geometry(
    faces_path: Path,
    labels: set[int],
    points: list[tuple[float, float, float]],
) -> tuple[dict[int, tuple[float, float, float]], list[tuple[float, float, float]]]:
    centroids: dict[int, tuple[float, float, float]] = {}
    vertices: list[tuple[float, float, float]] = []
    if not labels or not points:
        return centroids, vertices
    face_re = re.compile(r"^\s*\d+\s*\(([^)]*)\)\s*$")
    for face_index, line in enumerate(_read_foam_list_lines(faces_path)):
        if face_index not in labels:
            continue
        match = face_re.match(line)
        if not match:
            continue
        point_ids = [int(value) for value in match.group(1).split()]
        if not point_ids or any(point_id >= len(points) for point_id in point_ids):
            continue
        coords = [points[point_id] for point_id in point_ids]
        vertices.extend(coords)
        centroids[face_index] = (
            sum(coord[0] for coord in coords) / len(coords),
            sum(coord[1] for coord in coords) / len(coords),
            sum(coord[2] for coord in coords) / len(coords),
        )
    return centroids, vertices


def _centroid_summary(
    centroids: dict[int, tuple[float, float, float]],
    vertices: list[tuple[float, float, float]],
    label_count: int,
) -> dict[str, Any]:
    values = list(centroids.values())
    if not values:
        return {
            "face_count": label_count,
            "located_face_count": 0,
            "missing_face_count": label_count,
            "reason": "No skew-face centroids could be resolved from polyMesh faces and points.",
        }
    bbox_source = vertices or values
    bbox_min = [min(value[axis] for value in bbox_source) for axis in range(3)]
    bbox_max = [max(value[axis] for value in bbox_source) for axis in range(3)]
    centroid_mean = [sum(value[axis] for value in values) / len(values) for axis in range(3)]
    sample_centroids = [
        {"face": face_id, "centroid": list(centroid)}
        for face_id, centroid in sorted(centroids.items())[:5]
    ]
    return {
        "face_count": label_count,
        "located_face_count": len(values),
        "missing_face_count": label_count - len(values),
        "bbox_min": bbox_min,
        "bbox_max": bbox_max,
        "centroid_mean": centroid_mean,
        "sample_centroids": sample_centroids,
    }


def _skew_faces_by_processor(output_dir: Path) -> dict[str, int]:
    case_dir = output_dir / "case"
    counts: dict[str, int] = {}
    for path in sorted(case_dir.glob("processor*/constant/polyMesh/sets/skewFaces")):
        count = _read_face_set_count(path)
        if count is not None:
            counts[path.parts[-5]] = count
    serial_count = _read_face_set_count(case_dir / "constant" / "polyMesh" / "sets" / "skewFaces")
    if serial_count is not None:
        counts["serial"] = serial_count
    return counts


def _skew_face_geometry_by_processor(output_dir: Path) -> dict[str, dict[str, Any]]:
    case_dir = output_dir / "case"
    summaries: dict[str, dict[str, Any]] = {}
    poly_mesh_dirs = sorted(case_dir.glob("processor*/constant/polyMesh"))
    serial_poly_mesh = case_dir / "constant" / "polyMesh"
    if serial_poly_mesh.exists():
        poly_mesh_dirs.append(serial_poly_mesh)
    for poly_mesh_dir in poly_mesh_dirs:
        set_path = poly_mesh_dir / "sets" / "skewFaces"
        labels = _read_label_list(set_path)
        if not labels:
            continue
        processor = poly_mesh_dir.parts[-3] if poly_mesh_dir.parts[-3].startswith("processor") else "serial"
        points = _read_points(poly_mesh_dir / "points")
        centroids, vertices = _face_geometry(poly_mesh_dir / "faces", set(labels), points)
        summaries[processor] = _centroid_summary(centroids, vertices, len(labels))
    return summaries


def build_runtime_metrics(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    logs = {Path(item["log"]).name: item["log"] for item in runtime.get("commands", [])}
    snappy_log = _command_log(runtime, "snappyHexMesh", output_dir)
    check_mesh_log = _command_log(runtime, "checkMesh", output_dir)
    simplefoam_log = _command_log(runtime, "simpleFoam", output_dir)
    mesh_metrics = parse_mesh_logs(
        snappy_log.read_text(encoding="utf-8") if snappy_log.exists() else "",
        check_mesh_log.read_text(encoding="utf-8") if check_mesh_log.exists() else "",
    )
    skew_faces = _skew_faces_by_processor(output_dir)
    if skew_faces:
        mesh_metrics["skew_faces_by_processor"] = skew_faces
        mesh_metrics["skew_face_set_count"] = sum(skew_faces.values())
        expected_skew_count = int(mesh_metrics.get("highly_skew_face_count", 0))
        if expected_skew_count:
            mesh_metrics["skew_face_count_consistent_with_checkMesh"] = (
                mesh_metrics["skew_face_set_count"] == expected_skew_count
            )
    skew_geometry = _skew_face_geometry_by_processor(output_dir)
    if skew_geometry:
        mesh_metrics["skew_face_geometry_by_processor"] = skew_geometry
    mesh_metrics["configured_min_face_weight"] = config["mesh"]["quality"]["min_face_weight"]
    mesh_metrics["configured_snap_controls"] = config["mesh"]["snappy"].get("snap_controls", {})
    solver_metrics = parse_simplefoam_log(simplefoam_log.read_text(encoding="utf-8") if simplefoam_log.exists() else "")
    if config["function_objects"]["force_coefficients"]["enabled"]:
        force_metrics = write_force_metrics(config, output_dir)
    else:
        force_metrics = {
            "available": False,
            "required": False,
            "source": config["postprocess"]["force_extraction_source"],
            "reason": "forceCoeffs disabled for solver-only runtime isolation.",
        }
    if config["function_objects"]["y_plus"]["required"]:
        y_plus_log = _command_log(runtime, "yPlus", output_dir)
        y_plus_rows = read_y_plus_log(y_plus_log) if y_plus_log.exists() else []
        if y_plus_rows:
            y_plus_metrics = write_y_plus_summary(y_plus_rows, output_dir / "postprocess" / "yplus_summary.csv")
        else:
            y_plus_metrics = {"available": False, "reason": "OpenFOAM yPlus log summary was not found or could not be parsed."}
    else:
        y_plus_metrics = {
            "available": False,
            "required": False,
            "source": config["function_objects"]["y_plus"]["source_policy"],
            "reason": "yPlus disabled for solver-only runtime isolation.",
        }
    return {
        "schema_version": "openfoam_c04_metrics_v1",
        "parser": {
            "name": "openfoam_c04_motorbike_mesh_solver_force_parser",
            "version": 1,
            "limitations": [
                "Static readiness does not execute motorBike. Runtime validation requires native yPlus or an explicitly marked proxy source.",
            ],
        },
        "case_id": config["case_id"],
        "capability_id": config["capability_id"],
        "runtime": runtime,
        "mesh": mesh_metrics,
        "solver": solver_metrics,
        "postprocess": {"force_coefficients": force_metrics, "y_plus": y_plus_metrics},
        "artifacts": {
            "logs": logs,
            "metrics_json": str(output_dir / "metrics.json"),
            "validation_json": str(output_dir / "validation.json"),
            "validation_report": str(output_dir / "validation_report.md"),
        },
    }


def write_runtime_report(config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any], output_dir: Path) -> None:
    status = "passed" if validation["passed"] else "failed"
    forces = metrics.get("postprocess", {}).get("force_coefficients", {})
    y_plus = metrics.get("postprocess", {}).get("y_plus", {})
    lines = [
        f"# OpenFOAM C04 {config['case_id']} runtime report",
        "",
        f"- gate: `{validation['gate']}`",
        f"- status: `{status}`",
        f"- runtime profile: `{config['openfoam']['runtime_profile']}`",
        f"- Cd tail mean: `{forces.get('cd_tail_mean')}`",
        f"- Cl tail mean: `{forces.get('cl_tail_mean')}`",
        f"- y+ mean: `{y_plus.get('mean')}`",
        "",
        "## Scope",
        "",
        "This report covers motorBike mesh generation, simpleFoam execution, force coefficient extraction, and y+ validation only when runtime artifacts exist.",
    ]
    (output_dir / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime_outputs(config: dict[str, Any], output_dir: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    metrics = build_runtime_metrics(config, output_dir, runtime)
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_runtime_metrics(metrics, config, output_dir)
    validation_path = output_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_runtime_report(config, metrics, validation, output_dir)
    return {"metrics": metrics, "validation": validation, "metrics_path": metrics_path, "validation_path": validation_path}
