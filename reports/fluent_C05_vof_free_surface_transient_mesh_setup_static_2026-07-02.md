# Fluent C05 VOF Mesh Setup Static Readiness

Date: 2026-07-02

## Scope

This evidence closes the C05 official-source setup boundary for `vof.zip`.
It reads the official tutorial zip through `FLUENT_TUTORIAL_ROOT`, classifies archive entries, and confirms that the source package is mesh-only.

No Fluent VOF transient solve, alpha boundedness, phase conservation, interface motion, probe pressure, or dam-break benchmark validation is claimed.

## Result

- gate: static-readiness
- validation: passed
- archive entries: 1
- mesh entries: 1
- mesh format counts: `.msh: 1`
- total mesh bytes: 1889297
- solver replay status: `not_available_from_mesh_only_source`

## Artifacts

- `configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml`
- `schemas/fluent_C05_vof_free_surface_transient.schema.json`
- `src/science_capability_registry/fluent/vof_free_surface_transient/`
- `tests/test_fluent_c05_schema.py`
- `tests/test_fluent_c05_runner.py`
- `tests/test_fluent_c05_validation.py`
- `_results/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static/`

## Remaining Work

C05 needs a completed VOF setup contract or a separately labeled legacy case/data replay before transient runtime smoke can validate volume-fraction boundedness, phase volume conservation, interface position, and final-time behavior.
