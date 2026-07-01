from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


LEDGER_PATH = Path("reports/openfoam_failure_ledger.yaml")
EVIDENCE_INDEX_PATH = Path("reports/evidence_index.yaml")
LEDGER_SCHEMA_PATH = Path("schemas/openfoam_failure_ledger.schema.json")


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _repo_relative(path_value: str) -> bool:
    path = Path(path_value)
    return not path.is_absolute() and ":" not in path_value and "\\" not in path_value


def test_openfoam_failure_ledger_matches_schema() -> None:
    ledger = _read_yaml(LEDGER_PATH)
    schema = json.loads(LEDGER_SCHEMA_PATH.read_text(encoding="utf-8"))

    errors = sorted(
        Draft202012Validator(schema).iter_errors(ledger),
        key=lambda error: list(error.path),
    )

    assert not errors, [error.message for error in errors]


def test_openfoam_failure_ledger_structure_and_coverage() -> None:
    ledger = _read_yaml(LEDGER_PATH)

    assert ledger["ledger_id"] == "science_capability_registry.openfoam_failure_ledger"
    assert ledger["schema_version"] == "0.2.0"
    assert ledger["schema_path"] == LEDGER_SCHEMA_PATH.as_posix()
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
        assert entry["priority"] in {"P0", "P1", "P2", "P3"}
        assert entry["work_queue_status"] in {"active", "blocked", "gap", "mitigation_only", "resolved"}
        assert entry["owner_next_action"]
        assert isinstance(entry["blocked_by"], list)
        assert entry["confidence"] in {"high", "medium", "low"}
        assert str(entry["last_reviewed"]) == "2026-07-01"
        assert entry["evidence_refs"]
        assert entry["closure_criteria"]
        assert entry["do_not_claim"]
        for runtime_path in entry.get("runtime_evidence_paths", []):
            assert runtime_path.startswith("_results/openfoam/")
            assert _repo_relative(runtime_path)


def test_openfoam_failure_ledger_work_queue_resolves_entries() -> None:
    ledger = _read_yaml(LEDGER_PATH)
    entries_by_id = {entry["failure_id"]: entry for entry in ledger["entries"]}
    queued_ids: list[str] = []
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    for item in ledger["work_queue"]:
        assert item["acceptance_checks"]
        assert item["expected_evidence"]
        assert item["priority"] in {"P0", "P1", "P2", "P3"}
        queued_ids.extend(item["entry_failure_ids"])
        for failure_id in item["entry_failure_ids"]:
            assert failure_id in entries_by_id
            entry = entries_by_id[failure_id]
            assert priority_rank[item["priority"]] <= priority_rank[entry["priority"]]
            assert entry["work_queue_status"] != "resolved"

    assert len(queued_ids) == len(set(queued_ids))
    assert "OF-C04-F002-native-forcecoeffs-yplus-unvalidated" in queued_ids
    assert "OF-C05-F001-strouhal-target-mismatch" in queued_ids
    assert "OF-C08-F001-baseline-cfl-and-old-shock-window-failed" not in queued_ids


def test_openfoam_failure_ledger_priority_boundaries() -> None:
    ledger = _read_yaml(LEDGER_PATH)

    p0_ids = {entry["failure_id"] for entry in ledger["entries"] if entry["priority"] == "P0"}
    resolved_ids = {entry["failure_id"] for entry in ledger["entries"] if entry["work_queue_status"] == "resolved"}
    double_v_gaps = [
        entry for entry in ledger["entries"]
        if entry["state"] == "double_v_gap" and entry["benchmark_status_effect"] == "benchmark_validated_retained"
    ]

    assert p0_ids == {
        "OF-C04-F001-mesh-skewness-and-solver-smoke-failed",
        "OF-C04-F002-native-forcecoeffs-yplus-unvalidated",
        "OF-C05-F001-strouhal-target-mismatch",
    }
    assert resolved_ids == {
        "OF-C04-F001-mesh-skewness-and-solver-smoke-failed",
        "OF-C08-F001-baseline-cfl-and-old-shock-window-failed",
    }
    assert double_v_gaps
    assert {entry["priority"] for entry in double_v_gaps} == {"P2"}
    assert {entry["work_queue_status"] for entry in double_v_gaps} == {"gap"}


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
            if ref["evidence_level"] == "repo_stable_report":
                assert ref["evidence_id"] in evidence_by_id, (
                    f"{entry['failure_id']} references missing evidence_id "
                    f"{ref['evidence_id']}"
                )


def test_openfoam_failure_ledger_does_not_use_conversation_memory_as_evidence() -> None:
    ledger = _read_yaml(LEDGER_PATH)

    for entry in ledger["entries"]:
        for ref in entry["evidence_refs"]:
            assert ref["evidence_level"] != "conversation_memory"
