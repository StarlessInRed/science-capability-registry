from __future__ import annotations

import json
from pathlib import Path

from science_capability_registry.fluent.seed_suite.runner import run


def test_fluent_seed_suite_runner_dry_run_writes_static_artifacts(tmp_path: Path) -> None:
    result = run(
        config_path=Path("configs/fluent/seed_suite/c01_c08_static_readiness.yaml"),
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result["validated_config"] is True
    assert result["validation"]["passed"] is True
    assert result["metrics"]["seed_count"] == 8
    for rel_path in [
        "seed_suite_manifest.json",
        "seed_cases.json",
        "manifest.json",
        "metrics.json",
        "validation.json",
        "validation_report.md",
    ]:
        target = "seed_suite_manifest.json" if rel_path == "manifest.json" else rel_path
        assert (tmp_path / target).exists()

    seed_cases = json.loads((tmp_path / "seed_cases.json").read_text(encoding="utf-8"))
    assert [seed["seed_id"] for seed in seed_cases] == ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"]
    report = (tmp_path / "validation_report.md").read_text(encoding="utf-8")
    assert "does not launch Fluent" in report
