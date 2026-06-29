# OpenFOAM Solver Family Map

Use this map to avoid duplicate OpenFOAM capabilities.

## Initial Capability Set

| Capability | Slug | Solver family | Domain | First-phase priority |
| --- | --- | --- | --- | --- |
| C01 | `lid_driven_cavity_incompressible_laminar` | incompressible laminar steady or transient | CFD | yes |
| C02 | `potential_flow_cylinder_analytical_validation` | potential or inviscid flow | CFD | no |
| C03 | `backward_facing_step_rans_internal_flow` | incompressible RANS internal flow | CFD | yes |
| C04 | `external_aero_motorbike_rans_snappy` | external aerodynamics with snappyHexMesh | CFD | no |
| C05 | `transient_cylinder_vortex_shedding` | transient incompressible flow | CFD | no |
| C06 | `dam_break_vof_free_surface` | multiphase VOF free surface | multiphysics | yes |
| C07 | `conjugate_heat_transfer_cooling` | conjugate heat transfer | multiphysics | no |
| C08 | `compressible_shock_capturing_forward_step` | compressible transient shocks | CFD | no |

## Assignment Rules

- Reuse a capability when the solver family, physics class, validation target, and output quantities match.
- Create a new capability only for a materially different physics class, solver class, mesh workflow, or validation target.
- Prefer first-phase capabilities C01, C03, and C06 when building the initial OpenFOAM package examples.
