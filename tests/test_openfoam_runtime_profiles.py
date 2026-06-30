from __future__ import annotations

from pathlib import Path

import pytest

from science_capability_registry.openfoam.runtime_profiles import (
    load_runtime_profile,
    profile_path,
    validate_runtime_profile,
)
from science_capability_registry.openfoam.template_case import profile_env, resolve_runtime_identity


def test_openfoam_runtime_profile_catalog_validates() -> None:
    profiles = [
        load_runtime_profile(path)
        for path in sorted(Path("configs/openfoam/runtime_profiles").glob("*.yaml"))
    ]
    assert profiles
    profile_ids = {profile["profile_id"] for profile in profiles}
    assert "openfoam_com_v2112" in profile_ids
    assert "openfoam_com_v2112_cht" in profile_ids
    assert "openfoam_com_v2412" in profile_ids


def test_openfoam_runtime_profile_v2112_bindings() -> None:
    profile = load_runtime_profile(
        Path("configs/openfoam/runtime_profiles/openfoam_com_v2112.yaml")
    )

    assert profile["profile_id"] == "openfoam_com_v2112"
    assert profile["distribution"] == "openfoam_com"
    assert profile["backend"]["type"] == "wsl"
    assert profile["executable_bindings"]["incompressible_rans_steady"] == "simpleFoam"


def test_openfoam_runtime_profile_v2412_bindings() -> None:
    profile = load_runtime_profile(
        Path("configs/openfoam/runtime_profiles/openfoam_com_v2412.yaml")
    )

    assert profile["profile_id"] == "openfoam_com_v2412"
    assert profile["distribution"] == "openfoam_com"
    assert profile["version_label"] == "v2412"
    assert profile["backend"]["type"] == "wsl"
    assert profile["executable_bindings"]["vof_free_surface_transient"] == "interFoam"


def test_openfoam_runtime_profile_v2112_cht_bindings() -> None:
    profile = load_runtime_profile(
        Path("configs/openfoam/runtime_profiles/openfoam_com_v2112_cht.yaml")
    )

    assert profile["profile_id"] == "openfoam_com_v2112_cht"
    assert profile["distribution"] == "openfoam_com"
    assert profile["case_layout"] == "legacy_cht_multi_region"
    assert profile["backend"]["parallel"] is True
    assert profile["executable_bindings"]["cht_steady"] == "chtMultiRegionSimpleFoam"
    assert profile["executable_bindings"]["parallel_launcher"] == "mpirun"
    assert "splitMeshRegions" in profile["required_executables"]
    assert "changeDictionary" in profile["required_executables"]
    assert "faceAgglomerate" in profile["required_executables"]
    assert "viewFactorsGen" in profile["required_executables"]
    assert "mpirun" in profile["required_executables"]
    assert "c07_cpu_cabinet" in profile["tutorial_roots"]
    assert "c07_multi_region_heater_radiation" in profile["tutorial_roots"]


def test_openfoam_runtime_profile_rejects_private_keys() -> None:
    profile = load_runtime_profile(
        Path("configs/openfoam/runtime_profiles/openfoam_com_v2112.yaml")
    )
    profile["_unexpected"] = "bad"

    with pytest.raises(ValueError, match="_unexpected"):
        validate_runtime_profile(profile)


def test_openfoam_runtime_profile_path_uses_catalog_dir() -> None:
    assert profile_path("openfoam_com_v2112").as_posix().endswith(
        "configs/openfoam/runtime_profiles/openfoam_com_v2112.yaml"
    )


def test_openfoam_template_runtime_identity_resolves_profile_fallback() -> None:
    config = {
        "openfoam": {
            "runtime_profile": "openfoam_com_v2112",
            "distribution": "openfoam_com",
            "version": "v2112",
            "case_layout": "single_region",
        },
        "backend": {"type": "dry_run_only"},
        "solver": {"command_sequence": ["blockMesh", "simpleFoam"]},
    }

    identity = resolve_runtime_identity(config)

    assert identity["wsl_distro"] == "Ubuntu-24.04"
    assert identity["bashrc_path"] == "/opt/OpenFOAM-v2112/etc/bashrc"
    assert "simpleFoam" in identity["required_executables"]


def test_openfoam_template_runtime_identity_rejects_missing_profile() -> None:
    config = {
        "openfoam": {
            "runtime_profile": "missing_profile",
            "bashrc_path": "/opt/OpenFOAM-v2112/etc/bashrc",
        },
        "backend": {"type": "wsl", "wsl_distro": "Ubuntu-24.04"},
        "solver": {"command_sequence": ["blockMesh"]},
    }

    with pytest.raises(ValueError, match="runtime profile not found"):
        resolve_runtime_identity(config)


def test_openfoam_template_runtime_identity_rejects_profile_conflict() -> None:
    config = {
        "openfoam": {
            "runtime_profile": "openfoam_com_v2112",
            "distribution": "openfoam_foundation",
            "version": "v2112",
            "case_layout": "single_region",
        },
        "backend": {"type": "wsl", "wsl_distro": "Ubuntu-24.04"},
        "solver": {"command_sequence": ["blockMesh"]},
    }

    with pytest.raises(ValueError, match="conflicts with config"):
        resolve_runtime_identity(config)


def test_openfoam_template_runtime_identity_rejects_unknown_executable_override() -> None:
    config = {
        "openfoam": {
            "runtime_profile": "openfoam_com_v2112",
            "distribution": "openfoam_com",
            "version": "v2112",
            "case_layout": "single_region",
            "required_executables": ["blockMesh", "unknownFoam"],
        },
        "backend": {"type": "wsl", "wsl_distro": "Ubuntu-24.04"},
        "solver": {"command_sequence": ["blockMesh"]},
    }

    with pytest.raises(ValueError, match="not declared by profile"):
        resolve_runtime_identity(config)


def test_openfoam_profile_env_rejects_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        returncode = 0
        stdout = "\n\n\n\n\n\n"
        stderr = ""

    monkeypatch.setattr(
        "science_capability_registry.openfoam.template_case.run_wsl",
        lambda distro, script, timeout_s: Result(),
    )

    with pytest.raises(RuntimeError, match="required environment keys"):
        profile_env("Ubuntu-24.04", "/bad/bashrc", 1.0)
