---
name: openfoam-case-contract
description: Design OpenFOAM capability run schemas, configs, and case-generation contracts for science-capability-registry. Use when Codex needs to map OpenFOAM case anatomy such as 0/, constant/, system/, mesh, fields, boundary conditions, numerics, runtime controls, outputs, and validation into strict JSON/YAML contracts and dry-run manifests.
---

# OpenFOAM Case Contract

Use this skill when an OpenFOAM capability needs a config-first contract before implementation. The output should let a runner generate or validate a case without hiding scientific choices in CLI flags.

## Workflow

1. Start from an accepted or review-ready OpenFOAM capability card.
2. Define the run schema under `schemas/` and baseline config under `configs/openfoam/<capability_slug>/`.
3. Represent scientific choices explicitly: geometry, mesh, fields, dimensions, materials, initial conditions, boundary conditions, solver, numerics, runtime controls, postprocess targets, and validation gates.
4. Require a `dry_run` path that writes a manifest of case files, commands, expected outputs, backend, and validation targets without running OpenFOAM.
5. Keep solver-native dictionaries generated from config. Do not treat copied tutorial folders as the canonical source.
6. Fail fast on unknown config keys, unsupported solver aliases, missing dimensions, missing boundary patches, and unpinned OpenFOAM distribution/version assumptions.

## Required Paths

- Run schema: `schemas/openfoam_<asset_id>.schema.json`
- Baseline config: `configs/openfoam/<capability_slug>/<case_id>.yaml`
- Package target: `src/science_capability_registry/openfoam/<capability_slug>/`
- Runtime target: `_results/openfoam/<capability_slug>/<case_id>/`

## Reference Routing

- Read `references/openfoam-case-directory-contract.md` before defining generated case layout.
- Read `references/openfoam-field-and-dimension-contract.md` when fields, dimensions, or material properties are part of the schema.
- Read `references/openfoam-boundary-condition-contract.md` before encoding patches or boundary condition choices.
- Read `references/openfoam-numerics-contract.md` before adding solver, scheme, control, or convergence settings.
- Read `references/openfoam-execution-backends.md` before exposing backend selection.

## Boundaries

This skill designs contracts and configs. It may create schemas and baseline configs, but it should not implement solver execution, parse logs, or mark a benchmark validated. Use `$openfoam-runner-postprocess` and `$openfoam-validation-review` after the contract is stable.
