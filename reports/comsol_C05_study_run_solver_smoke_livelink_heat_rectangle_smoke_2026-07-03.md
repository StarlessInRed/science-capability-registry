# COMSOL C05 LiveLink Heat Rectangle Solver Smoke

- capability_id: `multiphysics.comsol.study_run_solver_smoke`
- gate: `smoke`
- status: passed
- config: `configs/comsol/study_run_solver_smoke/local_livelink_heat_rectangle.yaml`
- runtime evidence: `_results/comsol/study_run_solver_smoke/local_livelink_heat_rectangle/`

## Result

The local MATLAB LiveLink smoke generated and assigned a 2D heat rectangle, ran a stationary COMSOL study, and wrote solver/dataset artifacts.

Key metrics:

- `matlab_return_code`: 0
- `runtime_status`: `matlab_livelink_solver_smoke_passed`
- `study_executed`: true
- `solver_completed`: true
- `dataset_count`: 1
- `temperature_probe`: approximately 300 K

## Boundary

This evidence proves generated-rectangle stationary solver completion and dataset creation only. It does not claim analytical field validation, official replay, double-v, or benchmark validation.
