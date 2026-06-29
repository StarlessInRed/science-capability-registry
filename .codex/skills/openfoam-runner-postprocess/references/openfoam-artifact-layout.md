# OpenFOAM Artifact Layout

Use a predictable layout under `_results/`.

## Runtime Layout

`_results/openfoam/<capability_slug>/<case_id>/`

Recommended children:

- `case/`: generated OpenFOAM case, when retained.
- `logs/`: command logs and parser diagnostics.
- `postprocess/`: extracted CSV and OpenFOAM postProcessing outputs.
- `plots/`: owner-facing figures.
- `manifest.json`: generated files and commands.
- `metrics.json`: machine-readable extracted metrics.
- `validation.json`: pass/fail details and thresholds.

## Git Policy

Do not commit large runtime outputs. Commit schemas, configs, source code, tests, and curated reports under `reports/`.

## Report Linkage

Reports should identify the result directory, config path, commit hash when known, OpenFOAM version, and backend.
