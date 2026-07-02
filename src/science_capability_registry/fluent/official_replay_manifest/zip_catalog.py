"""Read-only source package classification for Fluent replay candidates."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

COMPOUND_SUFFIXES = (
    ".cas.h5",
    ".dat.h5",
    ".msh.h5",
    ".dsco.pmdb",
    ".wbpz",
    ".cas",
    ".dat",
    ".msh",
    ".jou",
    ".csv",
    ".pdf",
    ".dsco",
)


def compound_extension(path_text: str) -> str:
    lower = path_text.lower()
    for suffix in COMPOUND_SUFFIXES:
        if lower.endswith(suffix):
            return suffix
    return Path(lower).suffix


def entry_kind(path_text: str) -> str:
    suffix = compound_extension(path_text)
    lower = path_text.lower()
    if suffix in {".cas", ".cas.h5"}:
        return "case"
    if suffix in {".dat", ".dat.h5"}:
        return "data"
    if suffix in {".msh", ".msh.h5"}:
        return "mesh"
    if suffix == ".jou":
        return "journal"
    if suffix == ".wbpz":
        return "workbench_archive"
    if suffix == ".pdf":
        return "reference_document"
    if suffix in {".dsco", ".dsco.pmdb"}:
        return "auxiliary_design_package"
    if suffix == ".csv" and ("reference_data/" in lower or "ref-" in Path(lower).name):
        return "reference_csv"
    if suffix == ".csv":
        return "design_or_table_csv"
    return "other"


def package_entrypoint_class(counts: dict[str, int]) -> str:
    if counts.get("workbench_archive", 0) > 0:
        return "workbench_project"
    if counts.get("reference_document", 0) > 0:
        return "reference_document"
    if counts.get("case", 0) > 0 and counts.get("data", 0) > 0:
        return "case_data_replay"
    if counts.get("case", 0) > 0:
        return "case_only_replay"
    if counts.get("mesh", 0) > 0:
        return "mesh_only_setup"
    if counts.get("auxiliary_design_package", 0) > 0:
        return "auxiliary_design_package"
    if counts.get("reference_csv", 0) > 0:
        return "reference_csv_set"
    return "unclassified"


def _entry_record(entry_path: str, size: int, compressed_size: int | None, crc32: int | None) -> dict[str, Any]:
    return {
        "entry_path": entry_path,
        "entry_kind": entry_kind(entry_path),
        "compound_extension": compound_extension(entry_path),
        "size": int(size),
        "compressed_size": int(compressed_size) if compressed_size is not None else None,
        "crc32": int(crc32) if crc32 is not None else None,
    }


def inspect_zip_archive(path: Path) -> list[dict[str, Any]]:
    entries = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            entries.append(_entry_record(info.filename, info.file_size, info.compress_size, info.CRC))
    return entries


def inspect_directory(path: Path) -> list[dict[str, Any]]:
    entries = []
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        rel_path = item.relative_to(path).as_posix()
        entries.append(_entry_record(rel_path, item.stat().st_size, None, None))
    return entries


def inspect_reference_file(path: Path) -> list[dict[str, Any]]:
    return [_entry_record(path.name, path.stat().st_size, None, None)]


def summarize_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    suffix_counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["entry_kind"]] = counts.get(entry["entry_kind"], 0) + 1
        suffix = entry["compound_extension"]
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
    return {
        "entry_count": len(entries),
        "entry_kind_counts": counts,
        "compound_extension_counts": suffix_counts,
        "entrypoint_class": package_entrypoint_class(counts),
    }
