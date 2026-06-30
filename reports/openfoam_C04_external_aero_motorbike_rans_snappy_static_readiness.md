# OpenFOAM C04 static-readiness report

## Scope

- capability: `C04_external_aero_motorbike_rans_snappy`
- gate: `static-readiness`
- solver family: OpenFOAM.com v2112 `simpleFoam + snappyHexMesh`
- tutorial source: `/opt/OpenFOAM-v2112/tutorials/incompressible/simpleFoam/motorBike`

This report records the package-skeleton readiness of C04. It does not claim local OpenFOAM mesh generation, solver execution, force coefficient validity, y+ validity, or benchmark validation.

## Implemented

- Runtime profile binding for the motorBike tutorial and C04 executables, including `surfaceFeatureExtract`, `snappyHexMesh`, `topoSet`, `patchSummary`, `mpirun`, reconstruction tools, `foamDictionary`, and `postProcess`.
- Strict run schema: `schemas/openfoam_C04_external_aero_motorbike_rans_snappy.schema.json`.
- Baseline and inlet-speed perturbation configs under `configs/openfoam/external_aero_motorbike_rans_snappy/`.
- Package entrypoint under `src/science_capability_registry/openfoam/external_aero_motorbike_rans_snappy/`.
- Dry-run manifest generation from the official tutorial template.
- Runner-side copy of `/opt/OpenFOAM-v2112/tutorials/resources/geometry/motorBike.obj.gz` into `case/constant/triSurface/`.
- Runner-side restore of `0.orig` to `0`.
- `controlDict` patching that keeps `forceCoeffs` and disables visualization-heavy functionObjects for static-readiness.
- Config-visible force normalization: `rhoInf`, `magUInf`, `Aref`, `lRef`, `CofR`, `dragDir`, and `liftDir`.
- y+ validation contract requiring native `postProcess -func yPlus` or an explicitly marked proxy source.

## Evidence

Static tests validate schema/config loading, dry-run manifest creation, motorBike geometry preparation, snappy workflow declaration, forceCoeffs contract, y+ contract, and synthetic runtime validation checks.

## Limitations

- No `surfaceFeatureExtract`, `snappyHexMesh`, `checkMesh`, or `simpleFoam` runtime metrics have been promoted in this report.
- No native `forceCoeffs` output has been validated for C04.
- No runtime y+ summary exists yet.
- No Cd/Cl reference policy or perturbation matrix has passed runtime validation.
