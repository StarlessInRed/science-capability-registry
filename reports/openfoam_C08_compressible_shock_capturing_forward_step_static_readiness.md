# OpenFOAM C08 static-readiness report

## Scope

- capability: `C08_compressible_shock_capturing_forward_step`
- gate: `static-readiness`
- solver family: OpenFOAM.com v2112 `rhoCentralFoam`
- tutorial source: `/opt/OpenFOAM-v2112/tutorials/compressible/rhoCentralFoam/forwardStep`

This report records the package-skeleton readiness of C08. It does not claim local OpenFOAM solver execution, benchmark validation, shock-reference agreement, or conservation validation.

## Implemented

- Runtime profile binding for `rhoCentralFoam` and the C08 forwardStep tutorial root.
- Strict run schema: `schemas/openfoam_C08_compressible_shock_capturing_forward_step.schema.json`.
- Baseline and reduced-CFL configs under `configs/openfoam/compressible_shock_capturing_forward_step/`.
- Package entrypoint under `src/science_capability_registry/openfoam/compressible_shock_capturing_forward_step/`.
- Dry-run manifest generation from the official tutorial template.
- Explicit handling of `rho` as a thermophysical runtime output, not as a fabricated initial `0/rho` field.
- Validation checks for manifest sections, generated files, solver identity, thermophysical model, field contract, sample lines, averaging windows, and CFL contract.
- Python postprocess helpers for pressure/density-gradient shock location, upstream/downstream state averages, jump ratios, normal-shock sanity bounds, and field-extrema summaries.

## Evidence

Static tests validate schema/config loading, dry-run manifest creation, reduced-CFL control patching, shock metric helpers, and synthetic runtime validation checks.

## Limitations

- No `rhoCentralFoam` runtime metrics have been promoted in this report.
- No runtime field sampling exists yet for actual shock profile extraction.
- Reference shock position and pressure/density jump targets are intentionally `null`; C08 cannot move to benchmark validation until those references or accepted baseline samples are configured and passed.
- Conservation metrics currently have a contract and validation gate, but no runtime extraction path.
