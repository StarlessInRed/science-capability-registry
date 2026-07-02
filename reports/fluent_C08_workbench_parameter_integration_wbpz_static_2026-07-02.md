# Fluent C08 Workbench Parameter WBPZ Static Readiness

Date: 2026-07-02

## Scope

This evidence closes the C08 Workbench source-preflight layer for `workbench_parameter.zip`.
It reads the outer tutorial zip, opens the nested `fluent-workbench-param.wbpz`, classifies Workbench project entries, parses current project parameters from the `.wbpj`, and records historical `DesignPointLog.csv` rows.

No RunWB2 execution, Workbench project migration, design-point update, result extraction, or standalone Fluent batch equivalence is claimed.

## Result

- gate: static-readiness
- validation: passed
- outer archive status: readable
- nested WBPZ status: readable
- nested entries: 13
- Workbench project version: 2020 R2
- Workbench build: 20.2.210.0
- current parameter count: 3
- current parameters: P1 `hcpos=90`, P2 `ftpos=25`, P3 `wsfpos=175`
- historical design-point rows: 6
- Workbench journals: 5
- geometry database entries: 2
- mesh database entries: 1
- `RUNWB2_EXE` configured for this static run: false

## Artifacts

- `configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml`
- `schemas/fluent_C08_workbench_parameter_integration.schema.json`
- `src/science_capability_registry/fluent/workbench_parameter_integration/`
- `tests/test_fluent_c08_schema.py`
- `tests/test_fluent_c08_runner.py`
- `tests/test_fluent_c08_validation.py`
- `_results/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static/`

## Remaining Work

C08 still needs an explicit `RUNWB2_EXE` runtime profile, copy-to-runtime project isolation, version-migration handling, and design-point update/export evidence before Workbench smoke can be promoted beyond static preflight.
