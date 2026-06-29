# Multi-Agent Roles

Use these roles only after one active `asset_id` is selected. Do not run agents on different capabilities in parallel.

## Source Agent

- Read official webpages, examples, papers, or benchmark notes.
- Extract problem type, governing model, solver, boundary/initial conditions, mesh or discretization, expected outputs, and validation evidence.
- Do not edit files.

## Spec Agent

- Draft or review `software/<software>/assets/<asset_id>.yaml`, `schemas/<software>_<asset_id>.schema.json`, and `tasks/<software>_<asset_id>_intern_task.md`.
- Ensure scientific choices are visible in config/schema fields.
- Do not touch runner code when another agent owns implementation.

## Implementation Agent

- Own one package path under `src/science_capability_registry/<software>/<capability_slug>/`.
- Implement `config.py`, `runner.py`, `postprocess.py`, `validation.py`, `report.py`, `cli.py`, and baseline configs.
- Do not edit another capability's package or shared schema without coordinator approval.

## Validation Agent

- Own pytest files, validation rules, perturbation configs, and gate evidence.
- Check positive examples and rejection examples.
- Require artifact completeness, finite numerical values, convergence status, and physical trend checks.

## Science Reviewer

- Review whether the model class, solver settings, mesh/discretization, boundary conditions, convergence, and trends are scientifically defensible.
- Treat screenshots and single scalar outputs as insufficient.

## Evidence Agent

- Convert `_results/<software>/<capability>/<case_id>/` evidence into committed `reports/` summaries.
- Do not commit large runtime output unless explicitly approved.
