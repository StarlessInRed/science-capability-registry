---
name: openfoam-runner-postprocess
description: Implement or review OpenFOAM capability runners, case generation, solver execution, log parsing, post-processing, artifacts, and CLI entrypoints in science-capability-registry. Use for one active OpenFOAM capability package under src/science_capability_registry/openfoam/ with config-first behavior and runtime evidence under _results/.
---

# OpenFOAM Runner Postprocess

Use this skill to turn a reviewed OpenFOAM case contract into executable package behavior. Work on one OpenFOAM capability at a time.

## Workflow

1. Load the capability config and validate it against the run schema before generating files.
2. Generate OpenFOAM case dictionaries from config into `_results/openfoam/<capability_slug>/<case_id>/case/`.
3. Support `--dry-run` first. Dry run must emit a manifest with generated files, planned commands, backend, expected outputs, and validation targets.
4. Execute mesh tools, decomposition tools, solver, reconstruction, and post-processing only through the configured backend.
5. Capture stdout/stderr and solver logs. Parse residuals, continuity, Courant number, mesh quality, field extrema, probes, and capability-specific metrics when present.
6. Write `metrics.json`, plots, CSV tables, logs, and a machine-readable validation summary under the runtime result directory.
7. Commit only stable code, configs, schemas, tests, and human reports. Do not commit large `_results/` solver output.

## Required Runtime Artifacts

- `manifest.json`
- `metrics.json`
- solver log files
- generated case snapshot or file manifest
- postprocess CSV files when numeric profiles or probe histories are expected
- plots for owner review when the capability card requires them
- validation summary with pass/fail, thresholds, and failure reasons

## Reference Routing

- Read `references/openfoam-runner-contract.md` before implementing package orchestration or CLI behavior.
- Read `references/openfoam-log-parsing.md` before parsing solver output.
- Read `references/openfoam-postprocess-metrics.md` before choosing extracted quantities.
- Read `references/openfoam-artifact-layout.md` before writing runtime files or reports.

## Boundaries

This skill implements runner and postprocess behavior. It must not broaden the capability scope, relax schema gates, or upgrade `benchmark_status` without validation evidence. Use `$openfoam-validation-review` for status promotion.
