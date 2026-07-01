# OpenFOAM C08 external shock reference policy - 2026-07-01

## Scope

本报告记录 C08 `compressible_shock_capturing_forward_step` 从 smoke closure 推进到 benchmark validation 的 reference policy。

- capability: `C08_compressible_shock_capturing_forward_step`
- current asset status: `package_skeleton_created`
- current passing smoke result: `_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced/`

## Current Boundary

The reduced-CFL runtime closes smoke-level execution:

- rhoCentralFoam reaches final time
- max Courant passes
- local leading-shock position and jump sanity pass
- artifact completeness passes
- boundary flux owner-cell proxy is available

This does not close benchmark promotion. The current shock reference is a local accepted-baseline smoke sample, not an external benchmark or independent reference.

## Policy

Promotion requires:

- external or independently reviewed shock position target
- external or independently reviewed pressure jump target
- external or independently reviewed density jump target
- native OpenFOAM flux or face-field flux parity against the current owner-cell proxy

The promotion gate must reject:

- `source_type: local_runtime_smoke` as promotion-grade evidence
- `smoke_reference_only` accepted baselines as external reference evidence
- owner-cell flux proxy without native or face-field parity

## Next Acceptance Checks

- Add promotion-grade reference config fields or a dedicated config.
- Preserve local accepted-baseline samples as smoke-only evidence.
- Add native/face-field flux parity runtime or postprocess test.
- Add mesh or Mach perturbation trend if the external reference requires sensitivity evidence.
