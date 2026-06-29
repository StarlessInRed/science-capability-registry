# OpenFOAM Postprocess Metrics

Choose metrics from the capability card and solver family.

## Common Metrics

- residual history and final residuals
- continuity or mass balance error
- Courant number history for transient runs
- mesh quality summary from `checkMesh`
- field extrema and boundedness
- probe time histories or profiles
- pressure drop for internal flow
- lift, drag, and force coefficients for external flow
- yPlus statistics for wall-resolved RANS
- phase volume and alpha bounds for VOF cases

## Output Formats

- JSON for automated validation.
- CSV for profiles, histories, and scalar tables.
- PNG or SVG plots for human review.
- Markdown report for owner-facing validation evidence.

## Rule

Every plotted quantity should have a numeric source artifact. Do not make plots the only persisted evidence.
