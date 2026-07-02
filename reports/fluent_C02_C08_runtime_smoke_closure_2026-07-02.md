# Fluent C02-C08 runtime smoke closure - 2026-07-02

## Scope

This report records the local Fluent 2025 R1/v251 closure work for C02-C08 after the initial Fluent seed-suite intake. It separates runtime/readability evidence from physics benchmark validation and records the failures that changed the implementation contracts.

## Results

| C | config | gate | status | key evidence | not claimed |
| --- | --- | --- | --- | --- | --- |
| C02 | `configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_pressure_solve_smoke.yaml` | smoke | passed | Axisymmetric laminar self-generated pipe solve converged; inlet/outlet area-weighted static pressure reports produced runtime pressure drop `12.706476 Pa`, relative error `0.240866796875` against the `10.24 Pa` analytical target. | VMFL005 benchmark promotion; fully developed parabolic inlet homology; official payload parity. |
| C03 | `configs/fluent/mesh_convergence_trend/c02_pressure_drop_refinement_runtime_smoke.yaml` | smoke | passed | Three solved mesh levels passed with pressure drops `[12.446862, 12.706476, 12.786843] Pa` and adjacent changes `[0.020857787288073165, 0.006324885042870971]`. | Official adaptation replay; analytical convergence proof; fully developed inlet-profile convergence. |
| C04 | `configs/fluent/external_aero_force_coefficients/fluent_aero_case_read_smoke.yaml` | smoke | passed | Official aero case reads in Fluent; `mesh/check` completes; Fluent errors `0`. | Force/Cp extraction and aero benchmark validation. |
| C05 | `configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_read_smoke.yaml` | smoke | passed | Official inkjet mesh reads in Fluent; `49200` cells; `mesh/check` completes; Fluent errors `0`. | VOF transient solve, alpha boundedness, interface motion, conservation. |
| C06 | `configs/fluent/sliding_rotating_mesh/sliding_mesh_axial_comp_mesh_read_smoke.yaml` | smoke | passed | Official axial compressor mesh reads in `3ddp`; `27712` cells; `mesh/check` completes; Fluent errors `0`. | Moving-zone setup, sliding interface, periodicity, transient history. |
| C07 | `configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_read_smoke.yaml` | smoke | passed | Official heat-exchanger case/data pair reads in Fluent; temperature range `299.99997-494.50212 K`; inlet/outlet area-weighted temperatures `{inlet: 300.0, outlet: 307.49261} K`; heat-transfer balance relative error `0.00013039714285594258`. | CHT interface continuity, battery thermal validation, benchmark-grade heat-transfer validation. |
| C08 | `configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml` | static-readiness | passed | WBPZ parsed; current parameter count `3`; Workbench project remains classified as WBPZ/static preflight evidence. | RunWB2 execution, project migration, design-point update, result extraction. |

## Failure Lessons

- C02: Fluent surface-integral pressure sampling uses `/report/surface-integrals/area-weighted-avg`, not the longer `area-weighted-average` token. The prompt contract is `surface`, `()`, variable, `Write to file? no`.
- C02: Fluent named expressions can be created through TUI, but the velocity-inlet prompt did not accept the named expression or a direct parabolic expression in this local route. The pressure smoke remains a uniform-inlet homology smoke, not VMFL005 benchmark validation.
- C03: a 50-iteration coarse run failed convergence, while `max_iterations: 100` closed the three-level pressure-trend smoke. Iteration budget belongs in config, not hidden in the runner.
- C04/C07: reading existing case or case/data files may not print mesh-import cell-count lines even when `mesh/check` succeeds. Cell count is optional for case-read smoke; `mesh/check`, return code, and Fluent error count are the gate.
- C04: Windows can briefly keep Fluent transcript handles open after process return. The shared batch helper now retries moving root `fluent-*.trn` artifacts instead of treating the open handle as a physics/runtime failure.
- C06: the official `sliding_mesh/axial_comp.msh` is 3D and must use `3ddp`; `2ddp` fails with a wrong-dimensions error.
- C07: heat-transfer flux tables contain divider rows made of dashes; parsers must require true numeric rows instead of accepting `[-+0-9.eE]+` for values.
- Empty `stderr.txt` is valid for successful Fluent runs and must not fail artifact completeness by itself.

## Remaining Boundary

These gates close local runtime/readability blockers for the first Fluent seed assets and promote C02/C03/C07 from pure skeleton/source readiness to concrete smoke-level postprocess evidence. They do not freeze Fluent as benchmark-complete. The next benchmark-oriented work is: C02 parabolic-inlet/reference homology, C04 force/Cp extraction, C05 completed VOF setup, C06 moving-zone setup, and C08 copied-project RunWB2 execution.
