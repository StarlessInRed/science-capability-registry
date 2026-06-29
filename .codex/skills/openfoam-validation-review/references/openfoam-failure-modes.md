# OpenFOAM Failure Modes

Record failures explicitly. Do not hide them behind broad tolerances.

## Common Failures

- solver divergence or residual stagnation
- floating point exception
- failed `checkMesh`
- missing or wrong patch type
- inconsistent boundary condition across fields
- unbounded pressure, velocity, temperature, turbulence field, or phase fraction
- excessive Courant number
- negative turbulence quantities
- missing functionObject output
- parser mismatch with the selected OpenFOAM distribution
- postprocess output exists but does not match the capability card

## Classification

- Setup failure: case generation, paths, backend, missing executable, or missing files.
- Numerical failure: divergence, bad mesh, unstable time step, or invalid schemes.
- Physical failure: outputs violate model constraints or expected trends.
- Evidence failure: run may have completed, but required metrics or artifacts are absent.

## Response

Set `benchmark_status` to `validation_failed` only when a package exists and required validation fails. If no package evidence exists, keep `benchmark_candidate` and record missing evidence.
