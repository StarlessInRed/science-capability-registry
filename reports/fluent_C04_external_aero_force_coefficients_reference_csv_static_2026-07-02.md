# Fluent C04 External Aero Reference CSV Static Readiness

Date: 2026-07-02

## Scope

This evidence closes the C04 source-data parser layer for `fluent_aero_tutorial.zip`.
It reads the official tutorial zip through `FLUENT_TUTORIAL_ROOT`, classifies archive entries, parses configured reference CSV tables, and writes a reproducible manifest under `_results/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static/`.

No Fluent solver replay, force report extraction, Cp comparison to a replayed field, or mesh-independent aerodynamic benchmark validation is claimed.

## Result

- gate: static-readiness
- validation: passed
- archive entries: 9
- case entries: 1
- mesh entries: 3
- design/table CSV entries: 2
- reference CSV entries: 3
- ONERA Cl-vs-AoA valid rows: 7
- ONERA Cp 7.5 deg section valid rows: 89
- IRT swept-wing Cp massflow 313 section valid rows: 39
- Cl curve monotonic non-decreasing: true

## Artifacts

- `configs/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static.yaml`
- `schemas/fluent_C04_external_aero_force_coefficients.schema.json`
- `src/science_capability_registry/fluent/external_aero_force_coefficients/`
- `tests/test_fluent_c04_schema.py`
- `tests/test_fluent_c04_runner.py`
- `tests/test_fluent_c04_validation.py`
- `_results/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static/`

## Remaining Work

C04 still needs a real Fluent replay path that declares geometry, AoA or flow condition, turbulence model, section station, and force/Cp extraction homology before Cd/Cl/Cp validation can be promoted beyond this parser layer.
