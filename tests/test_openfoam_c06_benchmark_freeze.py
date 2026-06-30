from __future__ import annotations

import hashlib
import json
from pathlib import Path


BENCHMARK_DIR = Path("benchmarks/openfoam_c06_dam_break_vof_free_surface")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_openfoam_c06_frozen_benchmark_manifest_and_metrics() -> None:
    manifest = _load_json(BENCHMARK_DIR / "benchmark_manifest.json")
    expected_metrics = _load_json(BENCHMARK_DIR / "expected_metrics.json")
    criteria = _load_json(BENCHMARK_DIR / "validation_criteria.json")

    assert manifest["schema_version"] == "benchmark_freeze_manifest_v1"
    assert manifest["benchmark_id"] == "openfoam_c06_dam_break_vof_free_surface"
    assert manifest["capability_id"] == "cfd.openfoam.dam_break_vof_free_surface"
    assert manifest["benchmark_status"] == "frozen_canonical"
    assert manifest["replay_contract"]["benchmark_entrypoint"] == "science-openfoam-c06-benchmark"

    required_cases = criteria["case_rules"]["required_case_ids"]
    assert required_cases == manifest["case_matrix"]["required_case_ids"]
    assert set(expected_metrics["cases"]) == set(required_cases)

    baseline = expected_metrics["cases"]["baseline_wsl_v2112"]
    mesh = expected_metrics["cases"]["mesh_refined_wsl_v2112"]
    gravity = expected_metrics["cases"]["gravity_half_wsl_v2112"]
    height = expected_metrics["cases"]["water_height_125pct_wsl_v2112"]
    assert baseline["validation_passed"] is True
    assert abs(mesh["front_x_m"] - baseline["front_x_m"]) <= 0.08
    assert gravity["front_x_m"] < baseline["front_x_m"]
    assert height["water_volume_m3"] > baseline["water_volume_m3"] * 1.15
    assert height["front_x_m"] >= baseline["front_x_m"] * 0.95


def test_openfoam_c06_frozen_reference_artifact_hashes() -> None:
    artifact_hash = _load_json(BENCHMARK_DIR / "artifact_hash.json")
    frozen_artifacts = artifact_hash["frozen_reference_artifacts"]

    assert "benchmark_manifest.json" in frozen_artifacts
    assert "expected_metrics.json" in frozen_artifacts
    assert "validation_criteria.json" in frozen_artifacts

    for relative_path, expected_hash in frozen_artifacts.items():
        path = BENCHMARK_DIR / relative_path
        assert path.exists()
        assert _sha256(path) == expected_hash


def test_openfoam_c06_frozen_benchmark_is_indexed() -> None:
    readme = Path("benchmarks/README.md").read_text(encoding="utf-8")
    assert "openfoam_c06_dam_break_vof_free_surface" in readme
    assert "scientific_ci_openfoam_c06" in readme
