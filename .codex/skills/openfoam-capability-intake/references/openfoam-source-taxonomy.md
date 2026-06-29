# OpenFOAM Source Taxonomy

Classify each source before writing an asset card.

## Distribution Fields

Record these fields when evidence exists:

- `openfoam_distribution`: `openfoam_com`, `openfoam_foundation`, `openfoam_dev`, or `unknown`
- `openfoam_version`: exact version, release line, commit, or `unverified`
- `source_url`: canonical page or repository URL
- `tutorial_path`: tutorial case path when available
- `solver`: solver name as written by the source
- `solver_alias_policy`: use `reject_unpinned` when aliases differ between distributions

## Source Types

- Official tutorial: credible benchmark candidate, but not automatically validated.
- Solver documentation: capability evidence for model class, equations, and limitations.
- User blog or forum: weak evidence; require official docs or reproducible case before asset acceptance.
- Paper or benchmark report: strong validation evidence if geometry, mesh, BC, and reference outputs are available.
- Existing local package output: status evidence only if logs, metrics, and reports are present.

## Intake Rule

Treat webpages as evidence, not tutorials. Extract what capability the source proves, not how a user manually clicks or copies files.
