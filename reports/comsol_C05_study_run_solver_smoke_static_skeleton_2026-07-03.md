# COMSOL C05 Study Run Solver Smoke Static Skeleton

Date: 2026-07-03

## Scope

This report records static-readiness for `multiphysics.comsol.study_run_solver_smoke`.

The package emits study and dataset contract artifacts for a future solver smoke. It does not run a COMSOL study, inspect solver convergence, create datasets, or claim physics or benchmark validation.

## Evidence

- Config: `configs/comsol/study_run_solver_smoke/static_contract.yaml`
- Schema: `schemas/comsol_C05_study_run_solver_smoke.schema.json`
- Package: `src/science_capability_registry/comsol/study_run_solver_smoke/`
- Shared runner: `src/science_capability_registry/comsol/static_contract.py`
- Runtime evidence path: `_results/comsol/study_run_solver_smoke/static_contract/`
- Gate: `static-readiness`
- Status: passed

## Artifacts

- `solver_manifest.json`
- `dataset_manifest.json`
- `manifest.json`
- `metrics.json`
- `validation.json`
- `validation_report.md`

## Limitations

- No COMSOL study or solver runtime is executed.
- Solver success, convergence, dataset values, result export, official replay, and benchmark validation remain future gates.
