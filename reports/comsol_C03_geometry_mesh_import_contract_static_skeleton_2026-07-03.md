# COMSOL C03 Geometry Mesh Import Contract Static Skeleton

Date: 2026-07-03

## Scope

This report records static-readiness for `multiphysics.comsol.geometry_mesh_import_contract`.

The package emits geometry, mesh, and selection-map contract artifacts. It does not execute COMSOL CAD import, mesh generation, selection creation, physics assignment, solver execution, official replay, or benchmark validation.

## Evidence

- Config: `configs/comsol/geometry_mesh_import_contract/static_contract.yaml`
- Schema: `schemas/comsol_C03_geometry_mesh_import_contract.schema.json`
- Package: `src/science_capability_registry/comsol/geometry_mesh_import_contract/`
- Shared runner: `src/science_capability_registry/comsol/static_contract.py`
- Runtime evidence path: `_results/comsol/geometry_mesh_import_contract/static_contract/`
- Gate: `static-readiness`
- Status: passed

## Artifacts

- `geometry_manifest.json`
- `mesh_manifest.json`
- `selection_map.json`
- `manifest.json`
- `metrics.json`
- `validation.json`
- `validation_report.md`

## Limitations

- No geometry runtime, CAD import, mesh generation, mesh-quality check, physics assignment, or solver run is claimed.
- C03 remains a handoff contract until a real COMSOL geometry/mesh runtime is promoted.
