"""Runner for Fluent C01 steady internal-flow runtime smoke."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, load_case_config, repo_relative_path, validate_case_config
from .report import write_validation_report
from .validation import collect_runtime_metrics, validate_metrics

SCHEMA_ID = "schemas/fluent_C01_steady_internal_flow_runtime.schema.json"


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


def _source_case_path(config: dict[str, Any], require_exists: bool) -> Path:
    root_env = config["source_case"]["source_root_env"]
    root_value = os.environ.get(root_env)
    if not root_value:
        if require_exists:
            raise ValueError(f"Missing required environment variable {root_env} for Fluent tutorial source root.")
        return Path(f"${root_env}") / config["source_case"]["case_rel_path"]
    path = Path(root_value) / config["source_case"]["case_rel_path"]
    if require_exists and not path.exists():
        raise FileNotFoundError(f"Fluent source case does not exist: {path}")
    return path


def _journal_text(config: dict[str, Any], source_case: Path, output_dir: Path, resolved_paths: bool) -> str:
    source_case_text = _to_fluent_path(source_case) if resolved_paths else source_case.as_posix()
    output_case = output_dir / "fluent_c01_output.cas.h5"
    output_case_text = _to_fluent_path(output_case) if resolved_paths else output_case.as_posix()
    lines = [
        f'/file/read-case-data "{source_case_text}"',
    ]
    lines.append(f"/solve/iterate {config['solver']['iteration_count']}")
    if config["solver"]["deactivate_invalid_report_clients"]:
        lines.append("yes")
    if config["reports"]["mass_flow"]["enabled"]:
        lines.append("/report/fluxes/mass-flow")
        lines.append("yes")
        lines.append("no")
    if config["solver"]["write_case_data"]:
        lines.append(f'/file/write-case-data "{output_case_text}"')
    lines.append("/exit yes")
    return "\n".join(lines) + "\n"


def _write_journal(config: dict[str, Any], output_dir: Path, source_case: Path, resolved_paths: bool) -> Path:
    journal_path = output_dir / "journal.jou"
    journal_path.write_text(_journal_text(config, source_case, output_dir, resolved_paths), encoding="ascii")
    return journal_path


def _build_manifest(config: dict[str, Any], output_dir: Path, generated_files: list[str], dry_run: bool) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": SCHEMA_ID,
        "validated_config": True,
        "output_dir": str(output_dir),
        "fluent": config["fluent"],
        "backend": config["backend"],
        "source_case": config["source_case"],
        "solver": config["solver"],
        "reports": config["reports"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "runtime_commands": [
            "fluent dimension_precision -g -tN -i journal.jou",
        ],
        "scope": "dry-run Fluent C01 journal contract" if dry_run else "local Fluent C01 batch runtime smoke",
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

    output_path = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    output_path.mkdir(parents=True, exist_ok=True)
    source_case = _source_case_path(config, require_exists=not dry_run)
    journal_path = _write_journal(config, output_path, source_case, resolved_paths=not dry_run)
    generated_files = ["journal.jou"]
    manifest = _build_manifest(config, output_path, generated_files, dry_run=dry_run)

    if dry_run:
        validation = {
            "passed": True,
            "gate": "static-readiness",
            "scope": "Fluent C01 dry-run journal contract only; no Fluent execution",
            "checks": [{"name": "journal.written", "passed": True, "details": str(journal_path)}],
        }
        manifest["validation"] = validation
        manifest_path = output_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    backend_type = config["backend"]["type"]
    if backend_type == "dry_run_only":
        raise ValueError("Fluent C01 dry_run_only backend requires dry_run=True.")
    if backend_type != "fluent_batch":
        raise NotImplementedError(f"Fluent C01 backend {backend_type!r} is not implemented.")

    return_code = _execute_fluent(config, output_path, journal_path)
    metrics = collect_runtime_metrics(config, output_path, return_code)
    metrics_path = output_path / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    validation = validate_metrics(metrics, config, output_path, check_artifacts=False)
    validation_path = output_path / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_path / "validation_report.md", config, metrics, validation)
    generated_files.extend(
        [
            "stdout.txt",
            "stderr.txt",
            "transcript.txt",
            "metrics.json",
            "validation.json",
            "validation_report.md",
            "manifest.json",
        ]
    )
    manifest["generated_files"] = generated_files
    manifest["runtime"] = {
        "return_code": return_code,
        "metrics_json": str(metrics_path),
        "validation_json": str(validation_path),
    }
    manifest["metrics"] = metrics
    manifest["validation"] = validation
    (output_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    validation = validate_metrics(metrics, config, output_path, check_artifacts=True)
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    write_validation_report(output_path / "validation_report.md", config, metrics, validation)
    manifest["validation"] = validation
    (output_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    return run(config_path=config_path, output_dir=output_dir, dry_run=True)
