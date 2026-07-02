# COMSOL C03 LiveLink Heat Rectangle Smoke

- capability_id: `multiphysics.comsol.geometry_mesh_import_contract`
- gate: `smoke`
- status: passed
- config: `configs/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle.yaml`
- runtime evidence: `_results/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle/`

## Result

The local MATLAB LiveLink smoke generated a 2D rectangle model, ran COMSOL geometry and mesh generation, and wrote `geometry_manifest.json`, `mesh_manifest.json`, and `selection_map.json`.

Key metrics:

- `matlab_return_code`: 0
- `runtime_status`: `matlab_livelink_geometry_mesh_passed`
- `geometry_created`: true
- `mesh_created`: true
- `selection_role_count`: 1
- `solver_executed`: false

## Boundary

This evidence proves generated-rectangle geometry, mesh, and selection-map runtime closure only. It does not claim CAD import robustness, mesh quality, physics assignment, solver execution, official replay, double-v, or benchmark validation.
