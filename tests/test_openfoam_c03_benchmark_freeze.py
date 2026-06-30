from __future__ import annotations

import hashlib
import json
from pathlib import Path


BENCHMARK_DIR = Path("benchmarks/openfoam_c03_backward_facing_step_rans_internal_flow")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_openfoam_c03_frozen_benchmark_manifest_and_metrics() -> None:
    manifest = _load_json(BENCHMARK_DIR / "benchmark_manifest.json")
    expected_metrics = _load_json(BENCHMARK_DIR / "expected_metrics.json")
    criteria = _load_json(BENCHMARK_DIR / "validation_criteria.json")

    assert manifest["schema_version"] == "benchmark_freeze_manifest_v1"
    assert manifest["benchmark_id"] == "openfoam_c03_backward_facing_step_rans_internal_flow"
    assert manifest["capability_id"] == "cfd.openfoam.backward_facing_step_rans_internal_flow"
    assert manifest["benchmark_status"] == "frozen_canonical"
    assert manifest["replay_contract"]["benchmark_entrypoint"] == "science-openfoam-c03-benchmark"

    required_cases = criteria["case_rules"]["required_case_ids"]
    assert required_cases == manifest["case_matrix"]["required_case_ids"]
    assert set(expected_metrics["cases"]) == set(required_cases)

    baseline = expected_metrics["cases"]["baseline_wsl_v2112"]
    high = expected_metrics["cases"]["inlet_velocity_high_wsl_v2112"]
    low = expected_metrics["cases"]["inlet_velocity_low_wsl_v2112"]
    mesh = expected_metrics["cases"]["mesh_refined_wsl_v2112"]
    assert baseline["validation_passed"] is True
    assert mesh["pressure_drop_kinematic_m2_s2"] < baseline["pressure_drop_kinematic_m2_s2"]
    assert high["pressure_drop_kinematic_m2_s2"] > baseline["pressure_drop_kinematic_m2_s2"] * 1.3
    assert low["pressure_drop_kinematic_m2_s2"] < baseline["pressure_drop_kinematic_m2_s2"] * 0.9
    assert low["max_speed_m_s"] < baseline["max_speed_m_s"] < high["max_speed_m_s"]


def test_openfoam_c03_frozen_reference_artifact_hashes() -> None:
    artifact_hash = _load_json(BENCHMARK_DIR / "artifact_hash.json")
    frozen_artifacts = artifact_hash["frozen_reference_artifacts"]

    assert "benchmark_manifest.json" in frozen_artifacts
    assert "expected_metrics.json" in frozen_artifacts
    assert "validation_criteria.json" in frozen_artifacts

    for relative_path, expected_hash in frozen_artifacts.items():
        path = BENCHMARK_DIR / relative_path
        assert path.exists()
        assert _sha256(path) == expected_hash


def test_openfoam_c03_frozen_benchmark_is_indexed() -> None:
    readme = Path("benchmarks/README.md").read_text(encoding="utf-8")
    assert "openfoam_c03_backward_facing_step_rans_internal_flow" in readme
    assert "scientific_ci_openfoam_c03" in readme
