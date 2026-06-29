---
name: science-capability-registry-workflow
description: Build and review science-capability-registry assets. Use when Codex turns scientific software webpages, official examples, benchmark cases, or papers into capability cards, configs, schemas, packages, intern tasks, validation reports, or multi-agent execution plans for this repository.
---

# Science Capability Registry Workflow

## Overview

Use this skill to keep this repository's capability assets executable, reviewable, and scientifically meaningful. A webpage is capability evidence; an official example is a benchmark candidate; an intern task is a reusable, parameterized, validated capability implementation.

## Core Workflow

1. Identify the software, domain, capability, and source evidence.
2. Search existing `software/<software>/assets/` and `software/<software>/examples_index.md` before creating a new asset.
3. Create or update the capability card, run config schema, baseline config, intern task, package entrypoint, tests, and validation report together.
4. Keep user-visible choices in `configs/` and `schemas/`; do not hide scientific choices in CLI flags or hardcoded runner branches.
5. Store runtime evidence under `_results/`; commit only stable summaries under `reports/`.
6. Validate with the smallest sufficient gate and report unverified risks explicitly.

## Required Paths

- Capability card: `software/<software>/assets/<asset_id>.yaml`
- Source index: `software/<software>/examples_index.md`
- Run config: `configs/<software>/<capability_slug>/<case_id>.yaml`
- Run schema: `schemas/<software>_<asset_id>.schema.json`
- Package: `src/science_capability_registry/<software>/<capability_slug>/`
- Tests: `tests/test_<software>_<short_id>_{schema,runner,validation}.py`
- Intern task: `tasks/<software>_<asset_id>_intern_task.md`
- Human report: `reports/<software>_<asset_id>_<case>_validation.md`
- Runtime evidence: `_results/<software>/<capability_slug>/<case_id>/`

## Capability Card Status

Use two lifecycle fields:

- `card_status`: `draft`, `review`, `accepted`, or `retired`
- `benchmark_status`: `not_applicable`, `benchmark_candidate`, `package_skeleton_created`, `benchmark_validated`, `validation_failed`, or `retired`

Do not write the old top-level `status` field. The schema gate must reject it.

## Multi-Agent Use

Only run multiple agents around one active capability at a time. Keep write sets disjoint.

- `source agent`: read official pages and extract model, benchmark, solver, boundary, and validation facts.
- `spec agent`: draft the asset card, config schema, task, and acceptance criteria.
- `implementation agent`: own `src/`, `configs/`, and CLI for one capability.
- `validation agent`: own validation logic, pytest cases, perturbation configs, and gate evidence.
- `science reviewer`: review governing model, boundary conditions, discretization, convergence, trends, and failure modes.
- `evidence agent`: summarize `_results/` into `reports/` without committing large runtime output.

Read `references/agent-roles.md` before delegating a multi-agent task.

## Validation Gates

Use the stable tiers from `references/validation-gates.md`: `static-readiness`, `smoke`, `targeted-regression`, `integration`, `double-v`, and `full-regression`.

For every capability, minimum acceptance is:

- asset card validates against `schemas/capability_card.schema.json`
- config validates against the capability run schema
- `--dry-run` validates without solver execution
- solver baseline produces `metrics.json` with `validation.passed=true`
- at least three perturbation cases have physical trend explanations unless explicitly scoped out
