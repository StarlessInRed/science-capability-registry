# COMSOL MATLAB driver C01-C06 capability map - 2026-07-02

## Scope

This report records the first static capability-map pass for COMSOL Multiphysics driven from MATLAB through LiveLink for MATLAB.

## Current Evidence

- `software/comsol/capability_map.md` defines C01-C06 as MATLAB-driver action surfaces.
- `software/comsol/examples_index.md` records source roles and runtime prohibitions.
- `software/comsol/assets/` contains six capability cards:
  - `C01_matlab_server_bridge_runtime`
  - `C02_model_construction_api_contract`
  - `C03_geometry_mesh_import_contract`
  - `C04_physics_boundary_assignment_contract`
  - `C05_study_run_solver_smoke`
  - `C06_result_extraction_postprocess_validation`
- `configs/comsol/seed_suite/c01_c06_static_readiness.yaml` and `schemas/comsol_seed_suite.schema.json` protect the first static-readiness contract.
- `tasks/comsol_C01_*.md` through `tasks/comsol_C06_*.md` define intern implementation tasks.

## Local Runtime Preflight

The current host did not expose `matlab` or `comsol` on PATH, and common `Program Files` probes for MATLAB/COMSOL returned false. Therefore this report does not claim COMSOL runtime smoke, model execution, study run, or analytical benchmark validation.

## First Gate Order

1. C01 environment preflight and minimal MATLAB-to-COMSOL bridge.
2. C02 model construction API contract.
3. C03 geometry/mesh/import/selection contract.
4. C04 physics/material/boundary assignment contract.
5. C05 study-run solver smoke.
6. C06 result extraction and downstream consumability.

## No-Claim Boundary

- No MATLAB/COMSOL runtime execution is claimed.
- No `.mph` official example replay is claimed.
- No COMSOL solver success, analytical benchmark, or multiphysics validation is claimed.
- No machine-specific executable path, license path, server secret, or Application Library absolute path is committed.
