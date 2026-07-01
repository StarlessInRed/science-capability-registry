from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


LEDGER_PATH = Path("reports/openfoam_failure_ledger.yaml")
EVIDENCE_INDEX_PATH = Path("reports/evidence_index.yaml")


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _repo_relative(path_value: str) -> bool:
    path = Path(path_value)
    return not path.is_absolute() and ":" not in path_value and "\\" not in path_value


def test_openfoam_failure_ledger_structure_and_coverage() -> None:
    ledger = _read_yaml(LEDGER_PATH)

    assert ledger["ledger_id"] == "science_capability_registry.openfoam_failure_ledger"
    assert ledger["schema_version"] == "0.1.0"
    assert ledger["index_role"] == "failure_classification"
    assert ledger["scope"] == "OpenFOAM C01-C08"
    assert ledger["source_policy"]["runtime_policy"].startswith("Runtime outputs under _results")

    entries = ledger["entries"]
    assert isinstance(entries, list)
    assert len(entries) >= 8
    assert {entry["cxx_group"] for entry in entries} == {
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
        "C06",
        "C07",
        "C08",
    }

    states = {entry["state"] for entry in entries}
    assert "active_failure" in states
    assert "double_v_gap" in states
    assert "promotion_blocker" in states

    for entry in entries:
        assert entry["failure_id"].startswith(f"OF-{entry['cxx_group']}-")
        assert entry["capability_id"].startswith("cfd.openfoam.")
        assert _repo_relative(entry["asset_path"])
        assert Path(entry["asset_path"]).exists()
        assert entry["confidence"] in {"high", "medium", "low"}
        assert str(entry["last_reviewed"]) == "2026-07-01"
        assert entry["evidence_refs"]
        assert entry["closure_criteria"]
        assert entry["do_not_claim"]
        for runtime_path in entry.get("runtime_evidence_paths", []):
            assert runtime_path.startswith("_results/openfoam/")
            assert _repo_relative(runtime_path)


def test_openfoam_failure_ledger_evidence_refs_resolve() -> None:
    ledger = _read_yaml(LEDGER_PATH)
    evidence_index = _read_yaml(EVIDENCE_INDEX_PATH)
    evidence_by_id = {
        entry["evidence_id"]: entry for entry in evidence_index["evidence"]
    }

    assert "openfoam_failure_ledger_2026-07-01" in evidence_by_id
    ledger_evidence = evidence_by_id["openfoam_failure_ledger_2026-07-01"]
    assert ledger_evidence["primary_evidence_path"] == str(LEDGER_PATH).replace("\\", "/")
    assert Path(ledger_evidence["primary_evidence_path"]).exists()
    assert ledger_evidence["status"] == "indexed"

    for entry in ledger["entries"]:
        for ref in entry["evidence_refs"]:
            assert ref["evidence_level"] == "repo_stable_report"
            assert ref["evidence_id"] in evidence_by_id, (
                f"{entry['failure_id']} references missing evidence_id "
                f"{ref['evidence_id']}"
            )


def test_openfoam_failure_ledger_does_not_use_conversation_memory_as_evidence() -> None:
    ledger = _read_yaml(LEDGER_PATH)

    for entry in ledger["entries"]:
        for ref in entry["evidence_refs"]:
            assert ref["evidence_level"] != "conversation_memory"
