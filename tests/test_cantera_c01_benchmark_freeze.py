from __future__ import annotations

import hashlib
import json
from pathlib import Path


BENCHMARK_DIR = Path("benchmarks/cantera_c01_constant_pressure_ignition")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_cantera_c01_frozen_benchmark_manifest_and_metrics() -> None:
    manifest = _load_json(BENCHMARK_DIR / "benchmark_manifest.json")
    expected_metrics = _load_json(BENCHMARK_DIR / "expected_metrics.json")
    criteria = _load_json(BENCHMARK_DIR / "validation_criteria.json")

    assert manifest["benchmark_id"] == "cantera_c01_constant_pressure_ignition"
    assert manifest["capability_id"] == "combustion.cantera.constant_pressure_ignition"
    assert manifest["solver"] == "Cantera"
    assert manifest["reference_config"] == "reference_config.yaml"

    summary = expected_metrics["summary"]
    assert summary["time_point_count"] == 162
    assert summary["ignition_delay_method"] == "max_temperature_derivative"
    assert 3.0e-4 < summary["ignition_delay_s"] < 3.3e-4
    assert 2600.0 < summary["final_temperature_k"] < 2700.0

    status_rules = criteria["status_rules"]
    assert status_rules["required_solver_backend"] == "Cantera"
    assert status_rules["required_evidence_status"] == "complete"


def test_cantera_c01_frozen_reference_artifact_hashes() -> None:
    artifact_hash = _load_json(BENCHMARK_DIR / "artifact_hash.json")
    frozen_artifacts = artifact_hash["frozen_reference_artifacts"]

    assert "reference_config.yaml" in frozen_artifacts
    assert "reference_outputs/ignition_profile.csv" in frozen_artifacts
    assert "reference_outputs/metrics_summary.json" in frozen_artifacts

    for relative_path, expected_hash in frozen_artifacts.items():
        path = BENCHMARK_DIR / relative_path
        assert path.exists()
        assert _sha256(path) == expected_hash
