# OpenFOAM C02 finite-domain diagnostic

Date: 2026-07-01

## Scope

This report records a diagnostic refinement of `cfd.openfoam.potential_flow_cylinder_analytical_validation`.

The original strict analytical profile remains failed: the official OpenFOAM.com v2112 `basic/potentialFoam/cylinder` tutorial is a finite half-domain case with symmetry and finite outer boundaries, so it should not be promoted by directly comparing the whole field and owner-cell cylinder `Cp` against the unbounded cylinder solution.

## Runtime Result

- Strict profile: `configs/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112.yaml`
- Diagnostic profile: `configs/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112.yaml`
- Strict evidence root: `_results/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112`
- Diagnostic evidence root: `_results/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112`

The strict runtime completes `blockMesh`, `checkMesh`, and `potentialFoam`, but fails the configured analytical gates:

- `velocity_l2_error=1.1647355770764016`
- `velocity_linf_error=6.912121724051375`
- `pressure_l2_error=0.1366400904374664`
- `cp_linf_error=1.6228866742770676`

## Diagnostic Interpretation

The largest velocity errors occur near the tutorial's intermediate circular/outer-domain transition, not at a clean unbounded-cylinder sampling surface. A mask scan over the existing CSV shows the configured thresholds are only reachable when sampling very far from the cylinder, for example `r>=2.05`, which mostly proves far-field recovery rather than cylinder analytical validation.

The new finite-domain diagnostic profile therefore uses `finite_domain_corrected_reference_required`. Under that strategy, validation checks solver execution, artifact completeness, and finite analytical-error extraction, but does not claim the unbounded analytical thresholds passed.

## Status

C02 remains `package_skeleton_created`.

The current repository state is now explicit:

- OpenFOAM runtime execution works for this tutorial.
- Python postprocess can extract finite velocity, pressure, and owner-cell `Cp` error metrics.
- The official finite-domain tutorial is not yet a benchmark-valid unbounded-cylinder analytical validation.
- Promotion requires a corrected finite-domain/reference solution, a defensible surface-pressure extraction, or a separate domain-expanded case with demonstrated convergence toward the unbounded analytical solution.
