# COMSOL C06 Result Extraction Postprocess Validation Static Skeleton

Date: 2026-07-03

## Scope

This report records static-readiness for `multiphysics.comsol.result_extraction_postprocess_validation`.

The package emits export, probe-table, and unit contract artifacts for future result extraction. It does not call `mphglobal`, `mphinterp`, `mpheval`, or any COMSOL result export runtime, and it does not claim finite probe values or benchmark validation.

## Evidence

- Config: `configs/comsol/result_extraction_postprocess_validation/static_contract.yaml`
- Schema: `schemas/comsol_C06_result_extraction_postprocess_validation.schema.json`
- Package: `src/science_capability_registry/comsol/result_extraction_postprocess_validation/`
- Shared runner: `src/science_capability_registry/comsol/static_contract.py`
- Runtime evidence path: `_results/comsol/result_extraction_postprocess_validation/static_contract/`
- Gate: `static-readiness`
- Status: passed

## Artifacts

- `export_manifest.json`
- `probes.csv`
- `units.json`
- `manifest.json`
- `metrics.json`
- `validation.json`
- `validation_report.md`

## Limitations

- No COMSOL result extraction or finite-value validation is executed.
- Solver success, physics correctness, official replay, downstream analysis results, and benchmark validation remain future gates.
