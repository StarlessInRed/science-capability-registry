# OpenFOAM C02 static-readiness report

## Scope

- capability: `C02_potential_flow_cylinder_analytical_validation`
- gate: `static-readiness`
- solver family: OpenFOAM.com v2112 `potentialFoam`
- tutorial source: `/opt/OpenFOAM-v2112/tutorials/basic/potentialFoam/cylinder`

This report records the package-skeleton readiness of C02. It does not claim local OpenFOAM solver execution, benchmark validation, or analytical error convergence.

## Implemented

- Runtime profile binding for `potentialFoam` and the C02 tutorial root.
- Strict run schema: `schemas/openfoam_C02_potential_flow_cylinder_analytical_validation.schema.json`.
- Baseline and mesh-refinement configs under `configs/openfoam/potential_flow_cylinder_analytical_validation/`.
- Package entrypoint under `src/science_capability_registry/openfoam/potential_flow_cylinder_analytical_validation/`.
- Dry-run manifest generation from the official tutorial template with `0.orig` restored to `0`.
- Python analytical formulas for cylinder potential-flow velocity, kinematic Bernoulli pressure, and surface `Cp(theta) = 1 - 4*sin(theta)^2`.
- Validation checks for manifest sections, generated files, solver identity, sample-set declarations, and disabled tutorial functionObjects.

## Evidence

Static tests validate schema/config loading, dry-run manifest creation, formula sanity checks, and synthetic analytical metric validation.

## Limitations

- No `potentialFoam` runtime metrics have been promoted in this report.
- The tutorial uses a half-domain symmetry setup; runtime analytical comparison must account for sampling buffers and finite-domain effects.
- The official coded `error` functionObject is intentionally not the package validation source; C02 uses Python analytical comparison for reproducible numeric evidence.
- C02 remains below `benchmark_validated` until runtime outputs, analytical error metrics, and mesh-refinement trends pass.
