# COMSOL C03-C06 Negative Validation - 2026-07-03

本报告记录 C03-C06 generated heat-rectangle runtime validator 的 targeted negative regression。测试不启动 MATLAB/COMSOL，只向共享 validator 注入坏 metrics，确认 runner 会拒绝常见坏 handoff/runtime artifact。

## Covered Failures

| capability | negative fixture | expected failed checks |
| --- | --- | --- |
| C03 `geometry_mesh_import_contract` | missing selection role count | `selection.roles_declared` |
| C04 `physics_boundary_assignment_contract` | incomplete boundary assignment and missing units | `boundary.assignments_complete`, `units.present` |
| C05 `study_run_solver_smoke` | solver failure, no dataset, nonzero MATLAB return code | `solver.completed`, `dataset.present`, `matlab.return_code` |
| C06 `result_extraction_postprocess_validation` | nonfinite probe, missing units, missing expected-temperature error | `probe.values_finite`, `units.present`, `probe.expected_constant_temperature` |

## Implementation Boundary

- Public helper: `science_capability_registry.comsol.heat_rectangle_livelink.validate_heat_rectangle_metrics`
- Tests: `tests/test_comsol_c03_c06_validation.py`
- Gate: `targeted-regression`

These checks prove failure localization only. They do not prove official replay, solver convergence, mesh quality, analytical field correctness, double-v, or benchmark validation.

## No Claims

C03-C06 keep `card_status: review`, `benchmark_status: package_skeleton_created`, catalog `dispatch_status: runtime_smoke_passed`, and catalog `current_gate: smoke`. Negative validation is supporting regression evidence and does not replace the passed generated heat-rectangle smoke evidence as the primary evidence.
