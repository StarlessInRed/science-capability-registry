from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(".")
MAP_PATH = ROOT / "software" / "fluent" / "capability_map.md"
INDEX_PATH = ROOT / "software" / "fluent" / "examples_index.md"
EVIDENCE_INDEX_PATH = ROOT / "reports" / "evidence_index.yaml"

FLUENT_ASSETS = {
    "C01": "software/fluent/assets/C01_steady_internal_flow_runtime.yaml",
    "C02": "software/fluent/assets/C02_verification_reference_validation.yaml",
    "C03": "software/fluent/assets/C03_mesh_convergence_trend.yaml",
    "C04": "software/fluent/assets/C04_external_aero_force_coefficients.yaml",
    "C05": "software/fluent/assets/C05_vof_free_surface_transient.yaml",
    "C06": "software/fluent/assets/C06_sliding_rotating_mesh.yaml",
    "C07": "software/fluent/assets/C07_heat_transfer_energy_balance.yaml",
    "C08": "software/fluent/assets/C08_workbench_parameter_integration.yaml",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_fluent_c01_c08_capability_map_links_assets_and_seed_suite() -> None:
    map_text = MAP_PATH.read_text(encoding="utf-8")
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    for c_id, asset_path in FLUENT_ASSETS.items():
        asset = _read_yaml(ROOT / asset_path)
        assert asset["software"] == "Fluent"
        assert asset["card_status"] == "review"
        assert asset["benchmark_status"] == "benchmark_candidate"
        assert asset_path in index_text
        assert c_id in map_text

    suite_config = ROOT / "configs/fluent/seed_suite/c01_c08_static_readiness.yaml"
    assert suite_config.exists()


def test_fluent_capability_map_evidence_entries_resolve() -> None:
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {entry["evidence_id"]: entry for entry in evidence_index["evidence"]}

    for evidence_id in [
        "fluent_C01_C08_source_intake_2026-07-02",
        "fluent_C01_C08_seed_suite_static_readiness_2026-07-02",
    ]:
        evidence = evidence_by_id[evidence_id]
        assert evidence["asset_path"] == MAP_PATH.as_posix()
        assert Path(evidence["primary_evidence_path"]).exists()
        for path in evidence["supporting_paths"]:
            assert Path(path).exists(), path
