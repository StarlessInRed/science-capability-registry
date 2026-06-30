# Gmsh C01 OpenFOAM import smoke - 2026-06-30

## Scope

This report records the local downstream import smoke for `meshing.gmsh.parametric_geometry_mesh_generation`.

- source config: `configs/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112.yaml`
- result root: `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/`
- Gmsh backend: Python API, `gmsh` 4.15.0
- downstream importer: OpenFOAM.com v2112 `gmshToFoam`
- gate: `smoke`
- status: passed

## Result

The runtime generated a thin 3D extruded channel mesh from the config-visible geometry contract and converted it with `gmshToFoam`.

- Gmsh mesh nodes: 300
- Gmsh volume elements: 744
- quality metric: `gmsh_minSICN`
- minimum quality proxy: 0.6184575105195067
- `gmshToFoam` return code: 0
- OpenFOAM polyMesh points: 300
- OpenFOAM polyMesh faces: 1786
- OpenFOAM owner entries: 1786
- OpenFOAM neighbour entries: 1190
- imported boundary names: `frontAndBack`, `wall`, `outlet`, `inlet`

## Artifacts

- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/case.geo`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/case.msh`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/mesh_summary.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/downstream_import_summary.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/constant/polyMesh/`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/validation.json`
- `_results/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112_20260630_003/validation_report.md`

## Decision

The previous blocker "downstream solver import smoke missing" is closed for Gmsh C01. The baseline 2D `.msh` remains useful as a Gmsh mesh-generation smoke, but OpenFOAM `gmshToFoam` requires 3D volume elements, so the downstream import config uses a thin 3D extrusion with explicit `frontAndBack` surface tagging.

Keep `benchmark_status: package_skeleton_created`. This smoke proves OpenFOAM importability and physical-group preservation, but it does not run a downstream CFD solve, perturbation matrix, or broader mesh-quality regression.
