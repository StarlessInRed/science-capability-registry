"""Shared OpenFOAM template-case runtime helpers."""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from science_capability_registry.openfoam.runtime_profiles import load_runtime_profile, profile_path


def run_wsl(distro: str, script: str, timeout_s: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", distro, "--", "bash", "-lc", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )


def map_windows_path_to_wsl(path: Path, distro: str, timeout_s: float) -> str:
    result = subprocess.run(
        ["wsl", "-d", distro, "--", "wslpath", "-a", path.resolve().as_posix()],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to map Windows path to WSL path: {detail}")
    return result.stdout.strip().splitlines()[0]


def profile_env(distro: str, bashrc_path: str, timeout_s: float) -> dict[str, str]:
    script = (
        f"test -f {shlex.quote(bashrc_path)} || exit 2; "
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1 || exit 3; "
        "printenv WM_PROJECT_VERSION; printenv WM_PROJECT_DIR; printenv FOAM_TUTORIALS; "
        "printenv FOAM_APPBIN; printenv FOAM_USER_APPBIN; printenv OPENFOAM; true"
    )
    result = run_wsl(distro, script, timeout_s)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to source OpenFOAM bashrc {bashrc_path!r}: {detail}")
    lines = result.stdout.splitlines()
    keys = [
        "WM_PROJECT_VERSION",
        "WM_PROJECT_DIR",
        "FOAM_TUTORIALS",
        "FOAM_APPBIN",
        "FOAM_USER_APPBIN",
        "OPENFOAM",
    ]
    env = {key: lines[index] if index < len(lines) else "" for index, key in enumerate(keys)}
    required_keys = ["WM_PROJECT_VERSION", "WM_PROJECT_DIR", "FOAM_APPBIN", "FOAM_USER_APPBIN"]
    missing = [key for key in required_keys if not env.get(key)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"OpenFOAM bashrc did not define required environment keys: {joined}")
    return env


def command_log_name(command: str, index: int | None = None) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", command).strip("_")
    if not safe:
        safe = "command"
    if len(safe) > 96:
        safe = safe[:96].rstrip("_")
    prefix = f"{index:02d}_" if index is not None else ""
    return f"log.{prefix}{safe}"


def reset_generated_case_dir(output_dir: Path) -> Path:
    root = output_dir.resolve()
    case_dir = (output_dir / "case").resolve()
    if case_dir.name != "case" or case_dir.parent != root:
        raise ValueError(f"Refusing to reset unexpected case directory: {case_dir}")
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.parent.mkdir(parents=True, exist_ok=True)
    return case_dir


def copy_template_case(
    distro: str,
    source_path: str,
    output_dir: Path,
    timeout_s: float,
) -> list[str]:
    output_root = output_dir.resolve()
    case_dir = reset_generated_case_dir(output_root)
    parent_linux = map_windows_path_to_wsl(case_dir.parent, distro, timeout_s)
    script = (
        f"test -d {shlex.quote(source_path)} && "
        f"mkdir -p {shlex.quote(parent_linux)} && "
        f"cp -a {shlex.quote(source_path)} {shlex.quote(parent_linux)}/case"
    )
    result = run_wsl(distro, script, timeout_s)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to copy OpenFOAM template case: {detail}")
    written: list[str] = []
    for path in sorted(case_dir.rglob("*")):
        try:
            is_file = path.is_file()
        except OSError:
            continue
        if is_file:
            written.append(path.relative_to(output_root).as_posix())
    return written


def resolve_runtime_identity(config: dict[str, Any]) -> dict[str, Any]:
    backend = config["backend"]
    openfoam = config["openfoam"]
    profile_id = openfoam.get("runtime_profile", "")
    profile: dict[str, Any] = {}
    profile_source = ""
    if profile_id:
        candidate = profile_path(profile_id)
        if candidate.exists():
            profile = load_runtime_profile(candidate)
            profile_source = str(candidate)
        else:
            raise ValueError(f"OpenFOAM runtime profile not found: {profile_id}")

    profile_backend = profile.get("backend", {}) if profile else {}
    distro = backend.get("wsl_distro") or profile_backend.get("wsl_distro")
    bashrc_path = openfoam.get("bashrc_path") or profile.get("bashrc_path")
    timeout_s = float(backend.get("timeout_s") or profile_backend.get("timeout_s") or 300)
    case_layout = openfoam.get("case_layout")
    profile_case_layout = profile.get("case_layout")
    if case_layout and profile_case_layout and case_layout != profile_case_layout:
        raise ValueError(
            f"OpenFOAM case layout mismatch for profile {profile_id!r}: "
            f"config={case_layout!r}, profile={profile_case_layout!r}"
        )
    if profile:
        comparisons = [
            ("distribution", openfoam.get("distribution"), profile.get("distribution")),
            ("version", openfoam.get("version"), profile.get("version_label")),
            ("bashrc_path", openfoam.get("bashrc_path"), profile.get("bashrc_path")),
            ("wsl_distro", backend.get("wsl_distro"), profile_backend.get("wsl_distro")),
        ]
        mismatches = [
            f"{name}: config={config_value!r}, profile={profile_value!r}"
            for name, config_value, profile_value in comparisons
            if config_value and profile_value and config_value != profile_value
        ]
        if mismatches:
            raise ValueError(
                f"OpenFOAM runtime profile {profile_id!r} conflicts with config: "
                + "; ".join(mismatches)
            )
    if not distro:
        raise ValueError("backend.wsl_distro or runtime profile backend.wsl_distro is required")
    if not bashrc_path:
        raise ValueError("openfoam.bashrc_path or runtime profile bashrc_path is required")

    required = openfoam.get("required_executables") or profile.get("required_executables")
    if not required:
        raise ValueError("OpenFOAM required_executables must be declared in config or runtime profile")
    if profile and openfoam.get("required_executables"):
        profile_required = set(profile.get("required_executables", []))
        config_required = set(openfoam["required_executables"])
        missing_from_profile = sorted(config_required - profile_required)
        if missing_from_profile:
            joined = ", ".join(missing_from_profile)
            raise ValueError(
                f"OpenFOAM config required_executables are not declared by profile {profile_id!r}: {joined}"
            )
    return {
        "runtime_profile": profile_id,
        "profile_source": profile_source,
        "distribution": openfoam.get("distribution") or profile.get("distribution"),
        "version": openfoam.get("version") or profile.get("version_label"),
        "wsl_distro": distro,
        "bashrc_path": bashrc_path,
        "timeout_s": timeout_s,
        "required_executables": required,
        "case_layout": case_layout or profile_case_layout,
    }


def run_openfoam_command(
    distro: str,
    bashrc_path: str,
    case_dir_linux: str,
    command: str,
    timeout_s: float,
    log_path: Path,
) -> dict[str, Any]:
    script = (
        f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
        f"cd {shlex.quote(case_dir_linux)}; "
        f"{command}"
    )
    result = run_wsl(distro, script, timeout_s)
    log_text = result.stdout
    if result.stderr:
        log_text += result.stderr
    log_path.write_text(log_text, encoding="utf-8")
    return {"command": command, "returncode": result.returncode, "log": str(log_path)}


def execute_command_sequence(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    runtime_identity = resolve_runtime_identity(config)
    distro = runtime_identity["wsl_distro"]
    bashrc_path = runtime_identity["bashrc_path"]
    timeout_s = runtime_identity["timeout_s"]
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    case_dir_linux = map_windows_path_to_wsl(output_dir / "case", distro, timeout_s)
    env = profile_env(distro, bashrc_path, timeout_s)

    executable_checks = {}
    required = runtime_identity["required_executables"]
    for executable in required:
        script = (
            f"source {shlex.quote(bashrc_path)} >/dev/null 2>&1; "
            f"command -v {shlex.quote(executable)}"
        )
        result = run_wsl(distro, script, timeout_s)
        executable_checks[executable] = {
            "returncode": result.returncode,
            "path": result.stdout.strip().splitlines()[0] if result.stdout.strip() else "",
        }
        if result.returncode != 0:
            raise RuntimeError(f"Required OpenFOAM executable not found: {executable}")

    command_results = []
    for index, command in enumerate(config["solver"]["command_sequence"], start=1):
        result = run_openfoam_command(
            distro=distro,
            bashrc_path=bashrc_path,
            case_dir_linux=case_dir_linux,
            command=command,
            timeout_s=timeout_s,
            log_path=logs_dir / command_log_name(command, index),
        )
        command_results.append(result)
        if result["returncode"] != 0:
            break

    return {
        "backend": "wsl",
        "runtime_profile": runtime_identity["runtime_profile"],
        "profile_source": runtime_identity["profile_source"],
        "wsl_distro": distro,
        "bashrc_path": bashrc_path,
        "profile_env": env,
        "case_dir_linux": case_dir_linux,
        "required_executables": executable_checks,
        "commands": command_results,
    }
