# OpenFOAM Validation Metrics

Validation should combine numerical health, physical correctness, and artifact completeness.

## Solver Health

- final residual thresholds by equation
- continuity or mass conservation error
- Courant number threshold for transient cases
- solver completion time or iteration
- absence of fatal errors and floating point exceptions

## Mesh And Discretization

- `checkMesh` pass/fail
- non-orthogonality, skewness, aspect ratio, and cell count thresholds where available
- mesh independence requirement for accepted benchmark-grade cases when reference values depend strongly on mesh

## Physics

- bounded fields, such as alpha in `[0, 1]`
- positive temperature, density, viscosity, turbulence quantities, and species fractions where applicable
- conservation of mass or phase volume when expected
- expected pressure, velocity, force, temperature, or interface trends under parameter changes

## Artifacts

- `manifest.json`
- `metrics.json`
- logs
- CSV/profile output when required
- plots when required
- human-readable report
