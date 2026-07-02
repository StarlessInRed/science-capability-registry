# Fluent C06 Sliding Rotating Mesh Setup Static Readiness

Date: 2026-07-02

## Scope

This evidence closes the C06 source setup boundary for `sliding_mesh.zip` and legacy `single_rotating.zip`.
It reads both zip archives through `FLUENT_TUTORIAL_ROOT`, classifies mesh entries, and verifies that both sources are mesh-only setup seeds.

No Fluent moving-zone setup, sliding-interface definition, transient solve, periodicity check, or rotating-machinery validation is claimed.

## Result

- gate: static-readiness
- validation: passed
- source packages: 2
- readable packages: 2
- mesh entries: 3
- mesh format counts: `.msh: 2`, `.msh.h5: 1`
- total mesh bytes: 3543356
- solver replay status: `not_available_from_mesh_only_sources`

## Artifacts

- `configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml`
- `schemas/fluent_C06_sliding_rotating_mesh.schema.json`
- `src/science_capability_registry/fluent/sliding_rotating_mesh/`
- `tests/test_fluent_c06_schema.py`
- `tests/test_fluent_c06_runner.py`
- `tests/test_fluent_c06_validation.py`
- `_results/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static/`

## Remaining Work

C06 needs generated or recovered moving-zone settings, interface pairing, time-step controls, and monitor extraction before sliding/rotating runtime smoke can be promoted.
