# COMSOL C04 LiveLink Heat Rectangle Smoke

- capability_id: `multiphysics.comsol.physics_boundary_assignment_contract`
- gate: `smoke`
- status: passed
- config: `configs/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle.yaml`
- runtime evidence: `_results/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle/`

## Result

The local MATLAB LiveLink smoke generated a 2D heat rectangle, assigned material properties, created the `HeatTransfer` physics interface, assigned an all-boundary fixed-temperature condition, and wrote assignment/unit handoff artifacts.

Key metrics:

- `matlab_return_code`: 0
- `runtime_status`: `matlab_livelink_assignment_passed`
- `material_assigned`: true
- `physics_created`: true
- `boundary_assignment_count`: 1
- `missing_boundary_assignment_count`: 0
- `missing_unit_count`: 0
- `solver_executed`: false

## Boundary

This evidence proves generated-rectangle material, physics, boundary, and unit assignment runtime closure only. It does not claim solver convergence, field correctness, official replay, double-v, or benchmark validation.
