---
name: openfoam-capability-intake
description: Convert OpenFOAM tutorials, official examples, docs, papers, or benchmark cases into science-capability-registry asset definitions. Use when Codex needs to identify OpenFOAM distribution, solver, domain, capability, benchmark evidence, governing model, mesh, boundary conditions, numerics, outputs, validation criteria, examples_index updates, or intern tasks without implementing runners.
---

# OpenFOAM Capability Intake

Use this skill at source intake stage. Turn OpenFOAM evidence into a capability asset, benchmark candidate, and intern task. Do not implement runner code from this skill.

## Workflow

1. Identify the source type, OpenFOAM distribution, version evidence, tutorial path, solver, and case family.
2. Search existing `software/openfoam/assets/`, `software/openfoam/examples_index.md`, and `software/openfoam/capability_map.md` before creating a new asset.
3. Map the source to an existing OpenFOAM capability when possible. Create a new capability only when the problem class, solver family, or validation target is materially different.
4. Draft or update the capability card with problem type, model class, mesh/discretization, initial and boundary conditions, numerics, outputs, benchmark evidence, validation criteria, integration path, risks, and limitations.
5. Register official tutorials as `benchmark_candidate` unless this repository already has runner metrics and validation reports that justify `benchmark_validated`.
6. Create or update the intern task so it is executable by an intern, reviewable by the owner, and integrable into the registry.
7. Update `software/openfoam/examples_index.md` and any capability map touched by the new evidence.

## Required Status Fields

Use `card_status` and `benchmark_status`. Do not write the retired top-level `status` field.

Valid benchmark status choices are the repository schema values:

- `not_applicable`
- `benchmark_candidate`
- `package_skeleton_created`
- `benchmark_validated`
- `validation_failed`
- `retired`

## Reference Routing

- Read `references/openfoam-source-taxonomy.md` when the source distribution, version, or tutorial family is unclear.
- Read `references/openfoam-solver-family-map.md` before assigning or creating an OpenFOAM capability id.
- Read `references/openfoam-capability-card-checklist.md` before writing asset cards or intern tasks.
- Read `references/openfoam-benchmark-evidence.md` before setting benchmark status or validation criteria.

## Boundaries

This skill may create or update assets, indexes, capability maps, and tasks. It must not create solver runners, case generators, post-processing code, or runtime artifacts. Use `$openfoam-case-contract`, `$openfoam-runner-postprocess`, and `$openfoam-validation-review` for those stages.
