# OpenFOAM Gate Matrix

Use the smallest gate that proves the requested change.

## Gates

- `static-readiness`: schemas, configs, asset cards, and imports validate without running OpenFOAM.
- `smoke`: dry run and a minimal local execution path complete.
- `targeted-regression`: baseline capability and affected perturbation cases pass.
- `integration`: backend, runner, postprocess, report, and registry paths work together.
- `double-v`: compare against independent reference data or a second solver/tool when available.
- `full-regression`: run all stable OpenFOAM capabilities.

## Selection

- Asset-only intake usually needs `static-readiness`.
- Schema and config changes need schema tests plus dry run.
- Runner changes need smoke or targeted regression.
- Benchmark status promotion needs targeted regression at minimum.
- Cross-backend or cross-capability changes may need integration or full regression.

## Reporting

Always report which gate ran, which evidence was not run, and what residual risk remains.
