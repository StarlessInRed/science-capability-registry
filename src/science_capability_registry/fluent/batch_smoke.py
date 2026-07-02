"""Shared helpers for small Fluent batch smoke probes."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def env_path(env_name: str, label: str) -> Path:
    value = os.environ.get(env_name)
    if not value:
        raise ValueError(f"Missing required environment variable {env_name} for {label}.")
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"{label} path from {env_name} does not exist: {path}")
    return path


def fluent_path(path: Path) -> str:
    return path.resolve().as_posix()


def extract_zip_entries(archive_path: Path, entries: list[str], output_dir: Path) -> list[Path]:
    extracted = []
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        for entry in entries:
            if entry not in names:
                raise FileNotFoundError(f"Archive entry not found: {entry}")
            target = output_dir / Path(entry).name
            with archive.open(entry) as source, target.open("wb") as sink:
                shutil.copyfileobj(source, sink)
            extracted.append(target)
    return extracted


def write_journal(path: Path, commands: list[str]) -> Path:
    path.write_text("\n".join(commands) + "\n", encoding="ascii")
    return path


def collect_root_fluent_artifacts(before: set[Path], output_dir: Path) -> None:
    after = set(REPO_ROOT.glob("fluent-*.trn")) | set(REPO_ROOT.glob("cleanup-fluent-*.bat"))
    for path in sorted(after - before):
        target = output_dir / path.name
        shutil.move(str(path), str(target))
        if path.suffix.lower() == ".trn":
            shutil.copyfile(target, output_dir / "transcript.txt")


def execute_fluent(config: dict[str, Any], output_dir: Path, journal_path: Path) -> int:
    fluent = config["fluent"]
    fluent_exe = env_path(fluent["executable_env"], "Fluent executable")
    args = [
        str(fluent_exe),
        fluent["dimension_precision"],
        *fluent["headless_flags"],
        f"-t{fluent['processor_count']}",
        fluent["journal_argument"],
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
    collect_root_fluent_artifacts(before, output_dir)
    if not (output_dir / "transcript.txt").exists():
        shutil.copyfile(stdout_path, output_dir / "transcript.txt")
    return result.returncode


def runtime_text(output_dir: Path) -> str:
    parts = []
    for name in ["stdout.txt", "stderr.txt", "transcript.txt"]:
        path = output_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def collect_mesh_metrics(output_dir: Path, return_code: int) -> dict[str, Any]:
    text = runtime_text(output_dir)
    face_counts: dict[str, int] = {}
    for match in re.finditer(r"\s+(\d+)\s+2D\s+([A-Za-z-]+)\s+faces,\s+zone\s+\d+", text):
        face_counts[match.group(2)] = face_counts.get(match.group(2), 0) + int(match.group(1))
    cell_matches = list(re.finditer(r"\s+(\d+)\s+(?:quadrilateral|triangular|mixed|polyhedral|hexahedral|tetrahedral)\s+cells,\s+zone\s+\d+", text))
    cell_count = sum(int(match.group(1)) for match in cell_matches) if cell_matches else None
    return {
        "fluent_return_code": return_code,
        "mesh_cell_count": cell_count,
        "mesh_face_counts": face_counts,
        "mesh_check_completed": "Checking mesh" in text and "Done." in text,
        "fluent_warning_count": text.count("Warning:"),
        "fluent_error_count": text.count("Error:"),
        "runtime_status": "fluent_batch_smoke_completed" if return_code == 0 else "fluent_batch_smoke_failed",
    }

