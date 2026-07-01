# OpenFOAM C04 v2412 motorBike snap probe - 2026-07-01

## Scope

本报告记录 C04 `external_aero_motorbike_rans_snappy` 在 OpenFOAM.com v2412 本机 profile 上的 cross-profile runtime 结果。

- capability: `C04_external_aero_motorbike_rans_snappy`
- config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_snap_probe_layer0_wsl_v2412.yaml`
- result root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_snap_probe_layer0_wsl_v2412`
- runtime profile: `openfoam_com_v2412`
- gate: `smoke`

## Result

The v2412 profile can execute the C04 motorBike path. All OpenFOAM commands completed with returncode `0`:

- `surfaceFeatureExtract`
- `blockMesh`
- `decomposePar`
- `snappyHexMesh`
- `topoSet`
- `patchSummary`
- `potentialFoam`
- `checkMesh`
- `simpleFoam`

The validation status is still failed because the mesh quality gate is not satisfied:

- failed checks: `mesh.checkMesh_ok`, `mesh.max_skewness`
- cell count: `325743`
- max non-orthogonality: `64.9975`
- max aspect ratio: `14.5015`
- max skewness: `11.0447`
- max skewness threshold: `4.0`
- highly skew faces from `checkMesh`: `32`
- skewFaces set count: `32`
- skew-face count consistency: `true`
- simpleFoam started: `true`
- solver fatal error detected: `false`
- max final residual: `0.0728374`

## Local Geometry Diagnostic

The C04 runtime parser now reads OpenFOAM `skewFaces` face sets in both multiline and inline list formats, then derives per-processor face counts, vertex bounding boxes, mean face centroids, and sample face centroids from `polyMesh/faces` and `polyMesh/points`.

For this v2412 run, skewFaces are localized on:

- `processor0`: 10 faces
- `processor1`: 6 faces
- `processor3`: 11 faces
- `processor4`: 5 faces

`processor2` and `processor5` have zero skewFaces. The geometry diagnostics are stored in `metrics.json` under `mesh.skew_face_geometry_by_processor`.

## Decision

This run separates C04 from a pure v2112-local execution problem:

- v2412 runtime setup is viable.
- v2412 short solver path is viable for this diagnostic configuration.
- the active blocker remains mesh skewness, not template copying, profile binding, or simpleFoam startup.
- forceCoeffs, Cd/Cl tail-window, and yPlus are still not validated because this diagnostic config intentionally disables them until a passing mesh profile exists.

C04 remains `package_skeleton_created`, and the relevant failure ledger item remains active.
