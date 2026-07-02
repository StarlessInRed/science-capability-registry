# COMSOL C06 LiveLink Heat Rectangle Result Extraction Smoke

- capability_id: `multiphysics.comsol.result_extraction_postprocess_validation`
- gate: `smoke`
- status: passed
- config: `configs/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle.yaml`
- runtime evidence: `_results/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle/`

## Result

The local MATLAB LiveLink smoke generated, assigned, and solved a 2D heat rectangle, then exported a finite temperature probe and units through `probes.csv`, `units.json`, and `export_manifest.json`.

Key metrics:

- `matlab_return_code`: 0
- `runtime_status`: `matlab_livelink_result_extraction_passed`
- `solver_completed`: true
- `dataset_count`: 1
- `exported_probe_count`: 1
- `finite_value_fraction`: 1.0
- `max_abs_temperature_error_K`: approximately `1.0e-12`

## Boundary

This evidence proves generated-rectangle finite probe extraction and unit export only. It does not claim official replay, double-v, broader multiphysics correctness, or benchmark validation.
