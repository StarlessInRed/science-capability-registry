# COMSOL C04 Physics Boundary Assignment Contract Static Skeleton

Date: 2026-07-03

## Scope

This report records static-readiness for `multiphysics.comsol.physics_boundary_assignment_contract`.

The package emits assignment and unit-policy contract artifacts. It does not instantiate a COMSOL physics interface, assign real COMSOL selections, run a solver, or claim convergence or benchmark validation.

## Evidence

- Config: `configs/comsol/physics_boundary_assignment_contract/static_contract.yaml`
- Schema: `schemas/comsol_C04_physics_boundary_assignment_contract.schema.json`
- Package: `src/science_capability_registry/comsol/physics_boundary_assignment_contract/`
- Shared runner: `src/science_capability_registry/comsol/static_contract.py`
- Runtime evidence path: `_results/comsol/physics_boundary_assignment_contract/static_contract/`
- Gate: `static-readiness`
- Status: passed

## Artifacts

- `physics_assignment_manifest.json`
- `boundary_assignment_manifest.json`
- `unit_policy.json`
- `manifest.json`
- `metrics.json`
- `validation.json`
- `validation_report.md`

## Limitations

- No COMSOL physics/material/BC/IC runtime assignment is claimed.
- Solver convergence, datasets, result extraction, official replay, and benchmark validation remain downstream.
