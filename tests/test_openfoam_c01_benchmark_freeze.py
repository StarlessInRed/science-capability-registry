from __future__ import annotations

import hashlib
import json
from pathlib import Path


BENCHMARK_DIR = Path("benchmarks/openfoam_c01_lid_driven_cavity")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_openfoam_c01_frozen_benchmark_manifest_and_metrics() -> None:
    manifest = _load_json(BENCHMARK_DIR / "benchmark_manifest.json")
    expected_metrics = _load_json(BENCHMARK_DIR / "expected_metrics.json")
    criteria = _load_json(BENCHMARK_DIR / "validation_criteria.json")

    assert manifest["schema_version"] == "benchmark_freeze_manifest_v1"
    assert manifest["benchmark_id"] == "openfoam_c01_lid_driven_cavity"
    assert manifest["capability_id"] == "cfd.openfoam.lid_driven_cavity_incompressible_laminar"
    assert manifest["benchmark_status"] == "frozen_canonical"
    assert manifest["replay_contract"]["benchmark_entrypoint"] == "science-openfoam-c01-benchmark"
    assert manifest["replay_contract"]["required_runtime_profile"] == "openfoam_com_v2112"
    assert manifest["case_matrix"]["required_case_ids"] == ["baseline_wsl_v2112"]

    assert expected_metrics["source_case_id"] == "baseline_wsl_v2112"
    assert expected_metrics["runtime_profile"] == "openfoam_com_v2112"
    assert expected_metrics["validation_source"]["passed"] is True
    for profile_name in criteria["postprocess_rules"]["required_profiles"]:
        assert profile_name in expected_metrics["postprocess"]["profiles"]


def test_openfoam_c01_frozen_reference_artifact_hashes() -> None:
    artifact_hash = _load_json(BENCHMARK_DIR / "artifact_hash.json")
    frozen_artifacts = artifact_hash["frozen_reference_artifacts"]

    assert "benchmark_manifest.json" in frozen_artifacts
    assert "expected_metrics.json" in frozen_artifacts
    assert "validation_criteria.json" in frozen_artifacts

    for relative_path, expected_hash in frozen_artifacts.items():
        path = BENCHMARK_DIR / relative_path
        assert path.exists()
        assert _sha256(path) == expected_hash


def test_openfoam_c01_frozen_benchmark_is_indexed() -> None:
    readme = Path("benchmarks/README.md").read_text(encoding="utf-8")
    assert "openfoam_c01_lid_driven_cavity" in readme
    assert "scientific_ci_openfoam_c01" in readme
