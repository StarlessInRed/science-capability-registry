# OpenFOAM Runner Contract

A runner turns a validated config into generated case files, solver execution, and artifacts.

## Runner Steps

1. Load config.
2. Validate against the run schema.
3. Resolve backend and OpenFOAM version expectation.
4. Generate case dictionaries.
5. Write dry-run manifest.
6. Stop if `dry_run` is requested.
7. Run mesh generation or mesh checks.
8. Run solver command sequence.
9. Run postprocess commands.
10. Parse logs and generated data.
11. Write metrics and validation summary.

## CLI Expectations

Support:

- `--config <path>`
- `--output-dir <path>`
- `--dry-run`
- `--backend <backend>`
- `--case-id <id>` when the config permits override

Avoid adding many workflow-specific CLI flags. Scientific choices should live in config.
