from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.official_replay_manifest.bindings import binding_errors
from science_capability_registry.fluent.official_replay_manifest.zip_catalog import compound_extension, entry_kind


def test_fluent_replay_manifest_classifier_handles_compound_suffixes() -> None:
    assert compound_extension("case/foo.cas.h5") == ".cas.h5"
    assert compound_extension("case/foo.dat.h5") == ".dat.h5"
    assert compound_extension("case/foo.msh.h5") == ".msh.h5"
    assert entry_kind("case/foo.cas.h5") == "case"
    assert entry_kind("case/foo.dat.h5") == "data"
    assert entry_kind("case/foo.msh.h5") == "mesh"
    assert entry_kind("reference_data/ref-wing.csv") == "reference_csv"
    assert entry_kind("project/fluent-workbench-param.wbpz") == "workbench_archive"


def test_fluent_replay_manifest_binding_errors_detect_duplicate_seed() -> None:
    config = yaml.safe_load(Path("configs/fluent/official_replay_manifest/c01_c08_sources.yaml").read_text(encoding="utf-8"))
    broken = deepcopy(config)
    broken["capability_bindings"][1]["seed_id"] = "C01"

    errors = binding_errors(broken)

    assert any("duplicate binding" in error for error in errors)
