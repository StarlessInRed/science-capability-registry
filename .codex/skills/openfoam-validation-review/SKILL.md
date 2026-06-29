---
name: openfoam-validation-review
description: Define or review OpenFOAM validation gates, pytest cases, metrics contracts, perturbation cases, and reports for science-capability-registry. Use when checking residuals, continuity, Courant number, mesh quality, boundedness, y+, forces, probes, conservation, physical trends, failure modes, artifact completeness, and benchmark_status promotion.
---

# OpenFOAM Validation Review

Use this skill to decide whether an OpenFOAM capability is scientifically acceptable and whether its lifecycle status can advance.

## Workflow

1. Read the capability card, run schema, baseline config, runner outputs, tests, and latest validation report.
2. Check that validation covers solver health, mesh/discretization, boundary conditions, physical constraints, numerical convergence, expected trends, and artifact completeness.
3. Require at least one baseline case plus capability-specific perturbation cases unless the capability card explicitly scopes them out.
4. Compare results against analytical values, official tutorial expectations, standard benchmark data, conservation laws, or documented physical trends.
5. Keep validation gates small and named. Use the repository gate names: `static-readiness`, `smoke`, `targeted-regression`, `integration`, `double-v`, and `full-regression`.
6. Promote `benchmark_status` only when evidence exists:
   - `benchmark_candidate`: credible source, no local package evidence.
   - `package_skeleton_created`: schema, config, package, and dry-run exist.
   - `benchmark_validated`: solver run metrics, report, and tests pass.
   - `validation_failed`: runner exists but required checks fail.
7. Record residual risks rather than silently lowering thresholds.

## Minimum Evidence

- capability card validates against `schemas/capability_card.schema.json`
- run config validates against its run schema
- dry run passes and emits a manifest
- baseline solver run emits `metrics.json`
- validation summary records pass/fail and threshold values
- perturbation cases include physical trend explanations
- human report summarizes source, setup, results, failures, and next steps

## Reference Routing

- Read `references/openfoam-validation-metrics.md` before choosing checks or thresholds.
- Read `references/openfoam-gate-matrix.md` before deciding which gate is sufficient.
- Read `references/openfoam-physical-trend-checks.md` before reviewing perturbation cases.
- Read `references/openfoam-failure-modes.md` before interpreting failed runs.

## Boundaries

This skill reviews and designs validation. It may update tests, reports, and status fields when evidence supports the change. It should not implement new runner features unless the user explicitly asks for a combined fix.
