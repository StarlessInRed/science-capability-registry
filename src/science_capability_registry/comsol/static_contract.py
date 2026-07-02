"""Shared static-readiness runner for COMSOL C03-C06 contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {config_path}")
    data["_config_path"] = str(config_path)
    return data


def load_schema(schema_path: str | Path) -> dict[str, Any]:
    path = Path(schema_path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON schema object in {path}")
    return data


def validate_static_config(config: dict[str, Any], schema_path: str | Path) -> dict[str, Any]:
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    public_config = {key: value for key, value in config.items() if key != "_config_path"}
    errors = sorted(validator.iter_errors(public_config), key=lambda error: error.path)
    if errors:
        messages = []
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            messages.append(f"{path}: {error.message}")
        raise ValueError("Invalid COMSOL static contract config:\n" + "\n".join(messages))
    return config


def load_static_config(path: str | Path, schema_path: str | Path) -> dict[str, Any]:
    return validate_static_config(load_yaml(path), schema_path)


def repo_relative_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _check(checks: list[dict[str, Any]], name: str, passed: bool, details: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "details": details})


def _write_contract_artifacts(config: dict[str, Any], output_dir: Path) -> list[str]:
    generated_files: list[str] = []
    for artifact in config["contract"]["artifacts"]:
        payload = {
            "capability_id": config["capability_id"],
            "case_id": config["case_id"],
            "stage": config["contract"]["stage"],
            "artifact_path": artifact["path"],
            "artifact_role": artifact["role"],
            "source_boundary": config["contract"]["source_boundary"],
            "declared_objects": config["contract"]["declared_objects"],
            "handoff_contract": config["contract"]["handoff_contract"],
            "no_claims": config["validation"]["no_claims"],
        }
        artifact_path = output_dir / artifact["path"]
        if artifact_path.suffix.lower() == ".csv":
            artifact_path.write_text(
                "artifact_path,artifact_role,stage,runtime_executed\n"
                f"{artifact['path']},{artifact['role']},{config['contract']['stage']},false\n",
                encoding="utf-8",
            )
        else:
            artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        generated_files.append(artifact["path"])
    return generated_files


def validate_static_manifest(manifest: dict[str, Any], config: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    _check(checks, "config.validated", bool(manifest["validated_config"]), "configuration schema accepted")
    _check(checks, "backend.dry_run_only", config["backend"]["type"] == "dry_run_only", config["backend"]["type"])
    _check(checks, "runtime.not_executed", manifest["runtime_executed"] is False, str(manifest["runtime_executed"]))
    _check(checks, "no_claims.present", bool(config["validation"]["no_claims"]), str(len(config["validation"]["no_claims"])))

    declared_roles = {item["role"] for item in config["contract"]["declared_objects"]}
    for role in config["validation"]["required_object_roles"]:
        _check(checks, f"object_role.present.{role}", role in declared_roles, json.dumps(sorted(declared_roles)))

    for section in config["validation"]["required_manifest_sections"]:
        _check(checks, f"manifest.section.{section}", section in manifest, f"required section {section}")

    generated_files = set(manifest["generated_files"])
    for rel_path in config["validation"]["required_artifacts"]:
        _check(checks, f"artifact.listed.{rel_path}", rel_path in generated_files, rel_path)

    if output_dir is not None:
        root = Path(output_dir)
        for rel_path in config["validation"]["required_artifacts"]:
            path = root / rel_path
            _check(checks, f"artifact.exists.{rel_path}", path.exists() and path.stat().st_size > 0, str(path))

    return {
        "passed": all(item["passed"] for item in checks),
        "gate": config["validation"]["gate"],
        "scope": config["contract"]["scope"],
        "checks": checks,
        "details": {
            "stage": config["contract"]["stage"],
            "no_claims": config["validation"]["no_claims"],
        },
    }


def summarize_static_metrics(config: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "capability_id": config["capability_id"],
        "case_id": config["case_id"],
        "validated_config": True,
        "runtime_executed": False,
        "declared_object_count": len(config["contract"]["declared_objects"]),
        "required_object_role_count": len(config["validation"]["required_object_roles"]),
        "artifact_count": len(config["contract"]["artifacts"]),
        "required_artifact_count": len(config["validation"]["required_artifacts"]),
        "no_claim_count": len(config["validation"]["no_claims"]),
        "validation": {
            "passed": bool(validation["passed"]),
            "gate": validation["gate"],
        },
    }


def write_static_report(path: str | Path, config: dict[str, Any], metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    status = "passed" if validation["passed"] else "failed"
    lines = [
        f"# COMSOL {config['asset_id']} {config['case_id']} validation report",
        "",
        f"- capability_id: {config['capability_id']}",
        f"- gate: {validation['gate']}",
        f"- status: {status}",
        f"- backend: {config['backend']['type']}",
        f"- runtime executed: {metrics['runtime_executed']}",
        f"- declared objects: {metrics['declared_object_count']}",
        f"- required artifacts: {metrics['required_artifact_count']}",
        "",
        "## Checks",
        "",
    ]
    for item in validation["checks"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['name']}: {mark}")
    lines.extend(["", "## Scope", "", config["contract"]["scope"]])
    lines.extend(["", "## No Claims", ""])
    for claim in config["validation"]["no_claims"]:
        lines.append(f"- {claim}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_static_contract(
    schema_path: str | Path,
    schema_id: str,
    *,
    config_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    dry_run: bool = True,
    backend: str | None = None,
) -> dict[str, Any]:
    if config is None:
        if config_path is None:
            raise ValueError("Either config_path or config must be provided.")
        config = load_static_config(config_path, schema_path)
    else:
        config = validate_static_config(config, schema_path)
    if backend is not None:
        config = {**config, "backend": {**config["backend"], "type": backend}}
        config = validate_static_config(config, schema_path)

    if not dry_run:
        raise ValueError(f"{config['asset_id']} currently supports static-readiness dry_run only.")
    if config["backend"]["type"] != "dry_run_only":
        raise NotImplementedError(f"COMSOL backend {config['backend']['type']!r} is not implemented.")

    output_path = Path(output_dir) if output_dir is not None else repo_relative_path(config["outputs"]["output_dir"])
    output_path.mkdir(parents=True, exist_ok=True)
    generated_files = _write_contract_artifacts(config, output_path)
    generated_files.extend(["metrics.json", "validation.json", "validation_report.md", "manifest.json"])
    manifest = {
        "capability_id": config["capability_id"],
        "asset_id": config["asset_id"],
        "case_id": config["case_id"],
        "source_config": config.get("_config_path"),
        "schema_id": schema_id,
        "validated_config": True,
        "runtime_executed": False,
        "backend": config["backend"],
        "contract": config["contract"],
        "generated_files": generated_files,
        "expected_outputs": config["outputs"]["expected_outputs"],
        "validation_targets": config["validation"],
        "scope": config["contract"]["scope"],
    }
    validation = validate_static_manifest(manifest, config)
    metrics = summarize_static_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (output_path / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (output_path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_static_report(output_path / "validation_report.md", config, metrics, validation)
    (output_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    validation = validate_static_manifest(manifest, config, output_path)
    metrics = summarize_static_metrics(config, validation)
    manifest["validation"] = validation
    manifest["metrics"] = metrics
    (output_path / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (output_path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_static_report(output_path / "validation_report.md", config, metrics, validation)
    (output_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
