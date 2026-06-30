"""Small OpenFOAM ASCII field and polyMesh readers for registry validation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
VECTOR_RE = re.compile(rf"\(\s*({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*\)")


@dataclass(frozen=True)
class CellGeometry:
    index: int
    center: tuple[float, float, float]
    volume: float


@dataclass(frozen=True)
class PatchFace:
    patch: str
    face_index: int
    owner_cell: int
    center: tuple[float, float, float]


def _strip_line_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def _extract_counted_lines(text: str, start_index: int = 0) -> tuple[int, list[str]]:
    lines = text[start_index:].splitlines()
    for index, line in enumerate(lines):
        count_match = re.fullmatch(r"\s*(\d+)\s*", line)
        if count_match is None:
            continue
        count = int(count_match.group(1))
        open_index = index + 1
        while open_index < len(lines) and not lines[open_index].strip():
            open_index += 1
        if open_index >= len(lines) or lines[open_index].strip() != "(":
            continue
        items: list[str] = []
        for item_line in lines[open_index + 1 :]:
            stripped = item_line.strip()
            if stripped.startswith(")"):
                return count, items
            if stripped:
                items.append(stripped)
    raise ValueError("Could not locate counted OpenFOAM list body")


def read_internal_scalars(path: str | Path) -> list[float]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    uniform = re.search(rf"internalField\s+uniform\s+({FLOAT_RE})\s*;", text)
    if uniform is not None:
        return [float(uniform.group(1))]
    marker = re.search(r"internalField\s+nonuniform\s+List<scalar>", text)
    if marker is None:
        raise ValueError(f"Could not locate scalar internalField in {path}")
    count, lines = _extract_counted_lines(text, marker.end())
    values = [float(value) for line in lines for value in re.findall(FLOAT_RE, line)]
    if len(values) != count:
        raise ValueError(f"Expected {count} scalars in {path}, found {len(values)}")
    return values


def read_internal_vectors(path: str | Path) -> list[tuple[float, float, float]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    uniform = re.search(rf"internalField\s+uniform\s+\(\s*({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*\)\s*;", text)
    if uniform is not None:
        return [(float(uniform.group(1)), float(uniform.group(2)), float(uniform.group(3)))]
    marker = re.search(r"internalField\s+nonuniform\s+List<vector>", text)
    if marker is None:
        raise ValueError(f"Could not locate vector internalField in {path}")
    count, lines = _extract_counted_lines(text, marker.end())
    vectors = []
    for line in lines:
        match = VECTOR_RE.search(line)
        if match is not None:
            vectors.append((float(match.group(1)), float(match.group(2)), float(match.group(3))))
    if len(vectors) != count:
        raise ValueError(f"Expected {count} vectors in {path}, found {len(vectors)}")
    return vectors


def expand_uniform_scalars(values: list[float], cell_count: int) -> list[float]:
    if len(values) == 1:
        return [values[0]] * cell_count
    if len(values) != cell_count:
        raise ValueError(f"Expected {cell_count} scalar values, found {len(values)}")
    return values


def expand_uniform_vectors(values: list[tuple[float, float, float]], cell_count: int) -> list[tuple[float, float, float]]:
    if len(values) == 1:
        return [values[0]] * cell_count
    if len(values) != cell_count:
        raise ValueError(f"Expected {cell_count} vector values, found {len(values)}")
    return values


def read_points(path: str | Path) -> list[tuple[float, float, float]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    count, lines = _extract_counted_lines(text)
    points = []
    for line in lines:
        match = VECTOR_RE.search(line)
        if match is not None:
            points.append((float(match.group(1)), float(match.group(2)), float(match.group(3))))
    if len(points) != count:
        raise ValueError(f"Expected {count} points in {path}, found {len(points)}")
    return points


def read_faces(path: str | Path) -> list[list[int]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    count, lines = _extract_counted_lines(text)
    faces = []
    for line in lines:
        match = re.search(r"\d+\s*\(([^)]*)\)", line)
        if match is not None:
            faces.append([int(value) for value in re.findall(r"\d+", match.group(1))])
    if len(faces) != count:
        raise ValueError(f"Expected {count} faces in {path}, found {len(faces)}")
    return faces


def read_label_list(path: str | Path) -> list[int]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    count, lines = _extract_counted_lines(text)
    labels = [int(value) for line in lines for value in re.findall(r"-?\d+", line)]
    if len(labels) != count:
        raise ValueError(f"Expected {count} labels in {path}, found {len(labels)}")
    return labels


def read_boundary(path: str | Path) -> dict[str, dict[str, int | str]]:
    text = _strip_line_comments(Path(path).read_text(encoding="utf-8", errors="replace"))
    patches: dict[str, dict[str, int | str]] = {}
    for match in re.finditer(r"(?m)^\s*([A-Za-z_][\w.]*)\s*\{(.*?)^\s*\}", text, re.DOTALL | re.MULTILINE):
        name = match.group(1)
        body = match.group(2)
        n_faces = re.search(r"nFaces\s+(\d+)\s*;", body)
        start_face = re.search(r"startFace\s+(\d+)\s*;", body)
        patch_type = re.search(r"type\s+([A-Za-z_][\w.]*)\s*;", body)
        if n_faces is None or start_face is None:
            continue
        patches[name] = {
            "type": patch_type.group(1) if patch_type else "",
            "nFaces": int(n_faces.group(1)),
            "startFace": int(start_face.group(1)),
        }
    return patches


def _mean_point(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
        sum(point[2] for point in points) / count,
    )


def _box_volume(points: list[tuple[float, float, float]]) -> float:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return max((max(xs) - min(xs)) * (max(ys) - min(ys)) * (max(zs) - min(zs)), 0.0)


def load_cell_geometry(case_dir: str | Path) -> list[CellGeometry]:
    poly = Path(case_dir) / "constant" / "polyMesh"
    points = read_points(poly / "points")
    faces = read_faces(poly / "faces")
    owner = read_label_list(poly / "owner")
    neighbour = read_label_list(poly / "neighbour")
    cell_count = max(owner + neighbour) + 1 if neighbour else max(owner) + 1
    cell_vertices = [set() for _ in range(cell_count)]
    for face_index, face in enumerate(faces):
        owner_cell = owner[face_index]
        cell_vertices[owner_cell].update(face)
        if face_index < len(neighbour):
            cell_vertices[neighbour[face_index]].update(face)
    cells = []
    for index, vertex_ids in enumerate(cell_vertices):
        vertex_points = [points[item] for item in sorted(vertex_ids)]
        cells.append(CellGeometry(index=index, center=_mean_point(vertex_points), volume=_box_volume(vertex_points)))
    return cells


def load_patch_faces(case_dir: str | Path, patch_name: str) -> list[PatchFace]:
    poly = Path(case_dir) / "constant" / "polyMesh"
    points = read_points(poly / "points")
    faces = read_faces(poly / "faces")
    owner = read_label_list(poly / "owner")
    boundary = read_boundary(poly / "boundary")
    if patch_name not in boundary:
        raise ValueError(f"Patch {patch_name!r} not found in {poly / 'boundary'}")
    patch = boundary[patch_name]
    start = int(patch["startFace"])
    stop = start + int(patch["nFaces"])
    patch_faces = []
    for face_index in range(start, stop):
        face_points = [points[item] for item in faces[face_index]]
        patch_faces.append(
            PatchFace(
                patch=patch_name,
                face_index=face_index,
                owner_cell=owner[face_index],
                center=_mean_point(face_points),
            )
        )
    return patch_faces


def vector_magnitude(vector: tuple[float, float, float]) -> float:
    return math.sqrt(vector[0] * vector[0] + vector[1] * vector[1] + vector[2] * vector[2])


def finite_values(values: list[float]) -> bool:
    return bool(values) and all(math.isfinite(value) for value in values)
