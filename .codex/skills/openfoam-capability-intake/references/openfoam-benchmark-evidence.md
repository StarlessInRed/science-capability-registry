# OpenFOAM Benchmark Evidence

Use evidence strength to decide `benchmark_status` and validation requirements.

## Evidence Hierarchy

1. Analytical solution or conservation identity with measurable tolerance.
2. Standard benchmark with published reference data.
3. Official tutorial with known geometry, mesh, solver, and outputs.
4. Solver documentation describing model scope and assumptions.
5. Local dry-run package output.
6. Local solver run with logs, metrics, plots, and validation report.

## Status Guidance

- Official tutorial only: `benchmark_candidate`.
- Schema, config, package skeleton, and dry-run manifest: `package_skeleton_created`.
- Local run with passing metrics and report: `benchmark_validated`.
- Local run with failed required metrics: `validation_failed`.

## Missing Evidence

If reference values are unavailable, define validation through solver health, conservation, boundedness, mesh quality, and perturbation trends. Record that the case is trend-validated rather than reference-data validated.
