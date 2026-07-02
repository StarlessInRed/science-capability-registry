# Fluent C02-C08 runtime smoke closure - 2026-07-02

## Scope

This report records the local Fluent 2025 R1/v251 closure work for C02-C08 after the initial Fluent seed-suite intake. It separates runtime/readability evidence from physics benchmark validation.

## Results

| C | config | gate | status | key evidence | not claimed |
| --- | --- | --- | --- | --- | --- |
| C02 | `configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_pressure_solve_smoke.yaml` | smoke | passed | Axisymmetric laminar self-generated pipe solve converged at iteration 47; final continuity residual `9.1709e-4`; Fluent errors `0`. | Pressure-drop value extraction and benchmark promotion. |
| C03 | `configs/fluent/mesh_convergence_trend/c01_c02_refinement_trend_static.yaml` | static-readiness | passed | Three-level refinement contract with cell counts `320`, `1280`, `5120`; failure classes are explicit. | Solved mesh convergence or adaptation validation. |
| C04 | `configs/fluent/external_aero_force_coefficients/fluent_aero_case_read_smoke.yaml` | smoke | passed | Official aero case reads in Fluent; `mesh/check` completes; Fluent errors `0`; reference CSV parser remains active. | Force/Cp extraction and aero benchmark validation. |
| C05 | `configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_read_smoke.yaml` | smoke | passed | Official inkjet mesh reads in Fluent; `49200` cells; `mesh/check` completes; Fluent errors `0`. | VOF transient solve, alpha boundedness, interface motion, conservation. |
| C06 | `configs/fluent/sliding_rotating_mesh/sliding_mesh_axial_comp_mesh_read_smoke.yaml` | smoke | passed | Official axial compressor mesh reads in `3ddp`; `27712` cells; `mesh/check` completes; Fluent errors `0`. | Moving-zone setup, sliding interface, periodicity, transient history. |
| C07 | `configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_read_smoke.yaml` | smoke | passed | Official heat-exchanger case/data pair reads in Fluent; `mesh/check` completes; Fluent errors `0`. | Temperature extrema, heat-rate balance, CHT or battery thermal validation. |
| C08 | `configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml` | static-readiness | passed | WBPZ parsed; `RUNWB2_EXE`, `FLUENT_EXE`, and `AWP_ROOT251` were injected through environment preflight; current parameter count `3`. | RunWB2 execution, project migration, design-point update, result extraction. |

## Failure Lessons

- C02: the velocity-inlet zone command must use `inlet`, not `(inlet)`. The parenthesized token is rejected as an invalid zone.
- C02: Fluent surface-integral TUI command spelling differs from generated Python TUI method names; pressure-drop extraction remains a prompt-contract task.
- C04/C07: reading existing case or case/data files may not print mesh import cell-count lines even when `mesh/check` succeeds. Cell count is optional for case-read smoke; `mesh/check` and zero Fluent errors are the gate.
- C06: the official `sliding_mesh/axial_comp.msh` is 3D and must use `3ddp`; `2ddp` fails with a wrong-dimensions error.
- Empty `stderr.txt` is valid for successful Fluent runs and must not fail artifact completeness by itself.

## Remaining Boundary

These gates close runtime/readability blockers for the first Fluent seed assets. They do not freeze Fluent as benchmark-complete. The next benchmark-oriented work is postprocess extraction and physics closure: C02 pressure-drop reports, C04 force/Cp reports, C05 completed VOF setup, C06 moving-zone setup, C07 thermal reports, and C08 copied-project RunWB2 execution.

