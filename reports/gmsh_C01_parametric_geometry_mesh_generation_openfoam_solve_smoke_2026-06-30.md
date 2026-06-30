# Gmsh C01 OpenFOAM solve smoke - 2026-06-30

## Scope

This report records the local downstream OpenFOAM solve smoke for `meshing.gmsh.parametric_geometry_mesh_generation`.

- source config: `configs/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112.yaml`
- result root: `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/`
- Gmsh backend: Python API
- downstream importer: OpenFOAM.com v2112 `gmshToFoam`
- downstream solver smoke: `checkMesh -constant`, `potentialFoam -writep`
- gate: `smoke`
- status: passed

## Result

The runtime generated a thin 3D extruded channel mesh, converted it with `gmshToFoam`, checked the imported polyMesh, and completed a minimal `potentialFoam` solve smoke.

- Gmsh mesh nodes: 300
- Gmsh volume elements: 744
- quality metric: `gmsh_minSICN`
- minimum quality proxy: 0.6184575105195067
- `gmshToFoam` return code: 0
- imported boundary names: `frontAndBack`, `wall`, `outlet`, `inlet`
- `checkMesh -constant` return code: 0
- checkMesh signal: `Mesh OK`
- `potentialFoam -writep` return code: 0
- solver completion signal: `End`
- max final residual: 0.00469562
- continuity error: 0.00618431
- interpolated velocity error: 0.579228

## Artifacts

- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/case.geo`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/case.msh`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/mesh_summary.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/downstream_import_summary.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/downstream_solve_summary.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/logs/log.checkMesh`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/logs/log.potentialFoam`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/validation.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_solve_wsl_v2112_20260630_003/validation_report.md`

## Decision

The previous blocker "downstream CFD solve smoke missing" is closed for Gmsh C01. The capability now proves that a config-generated Gmsh mesh can preserve physical groups through `gmshToFoam` and can be consumed by a minimal OpenFOAM solver.

Keep `benchmark_status: package_skeleton_created`. This smoke proves solver consumability, not mesh-quality regression, perturbation robustness, or benchmark-grade CFD accuracy.
