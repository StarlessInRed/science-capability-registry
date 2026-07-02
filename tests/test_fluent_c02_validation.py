from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from science_capability_registry.fluent.verification_reference_validation.config import validate_case_config
from science_capability_registry.fluent.verification_reference_validation.validation import validate_reference_contract


def _load_config() -> dict:
    data = yaml.safe_load(
        Path("configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml").read_text(
            encoding="utf-8"
        )
    )
    return validate_case_config(data)


def test_fluent_c02_validation_accepts_formula_reference() -> None:
    validation = validate_reference_contract(_load_config())

    assert validation["passed"] is True
    assert any(item["name"] == "reference.formula_recomputes_target" and item["passed"] for item in validation["checks"])


def test_fluent_c02_validation_rejects_geometry_formula_mismatch() -> None:
    config = deepcopy(_load_config())
    config["reference_formula"]["pressure_drop_inputs"]["diameter_m"] = 0.003

    validation = validate_reference_contract(config)

    assert validation["passed"] is False
    assert any(item["name"] == "reference.formula_matches_geometry" and not item["passed"] for item in validation["checks"])
