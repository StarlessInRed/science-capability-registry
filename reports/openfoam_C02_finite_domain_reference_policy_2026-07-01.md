# OpenFOAM C02 finite-domain reference policy - 2026-07-01

## Scope

本报告记录 C02 `potential_flow_cylinder_analytical_validation` 的 analytical closure 策略。当前 finite-domain diagnostic 只能证明 runtime 和 error extraction，不允许把无界圆柱解析解 claim 提前恢复。

- capability: `C02_potential_flow_cylinder_analytical_validation`
- current asset status: `package_skeleton_created`
- relevant config: `configs/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112.yaml`
- relevant result root: `_results/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112/`

## Current Boundary

The strict analytical gate failed against the unbounded-cylinder reference. The finite-domain diagnostic is valuable, but it has a narrow claim:

- solver execution works
- artifacts are emitted
- finite analytical-error metrics can be extracted
- benchmark validation is not claimed

## Policy

Before promotion, C02 must close one of two reference paths:

1. Corrected finite-domain reference.
   The reference must account for finite farfield boundaries and current OpenFOAM sampling locations.

2. Domain-expanded convergence reference.
   The case matrix must show velocity/Cp errors trending down as farfield domain size and mesh resolution improve.

In both paths, surface Cp source must be explicit. Owner-cell proxy pressure is not enough for a strict surface Cp claim unless an independent parity check is recorded.

## Next Acceptance Checks

- Add a domain-expanded or corrected-reference config.
- Add validation tests that keep finite-domain diagnostic non-promotional.
- Add a trend test or report for analytical error under domain/mesh changes.
- Keep `benchmark_validated` blocked until the reference path and surface Cp source are closed.
