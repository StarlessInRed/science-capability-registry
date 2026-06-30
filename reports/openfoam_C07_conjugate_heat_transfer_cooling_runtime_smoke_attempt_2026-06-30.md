# OpenFOAM C07 Runtime Smoke Attempt - 2026-06-30

## Summary

- capability_id: `cfd.openfoam.conjugate_heat_transfer_cooling`
- case_id: `baseline_cpu_cabinet_wsl_v2112`
- runtime profile: `openfoam_com_v2112_cht`
- backend: WSL `Ubuntu-24.04`
- source config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/runtime_smoke_wsl_v2112`
- status: failed

## Command Progress

The runtime path successfully completed the preprocessing and mesh gates:

- `blockMesh`: passed
- `surfaceFeatureExtract`: passed
- `snappyHexMesh -overwrite`: passed
- `decomposePar`: passed
- `restore0Dir -processor`: passed after using the absolute OpenFOAM `RunFunctions` path
- `splitMeshRegions -cellZones -overwrite -parallel`: passed after adding config-visible `mpirun --oversubscribe`
- `topoSet -region domain0 -parallel`: passed
- `checkMesh -allRegions -constant -parallel`: passed, with `Mesh OK`

The solver gate failed:

- `chtMultiRegionSimpleFoam -parallel`: failed with return code 136
- final parsed pseudo-time: 2.0
- fluid and solid region meshes were created for `domain0`, `v_CPU`, and `v_fins`
- detected failure: true floating-point exception, not the normal `trapFpe` startup notice
- stack signature: `compressibleTurbulenceModel::phi()` / `realizableKE::correct()` / `Foam::divide`

## Validation Outcome

The runtime validation correctly failed and did not promote the benchmark status.

Failed checks include:

- solver command return code
- no fatal error
- final time reaching configured `end_time_iterations: 200`
- final residual threshold
- reconstructed temperature field bounds
- interface proxy availability

Passing checks include:

- generated case file completeness
- mesh command return codes through `checkMesh`
- `checkMesh` mesh-ok signal
- expected static artifacts and metrics/validation/report files

## Residual Risk

This attempt proves the Windows/WSL/OpenFOAM.com v2112 command chain reaches the CHT solver, but it does not prove the CHT benchmark is physically valid. The next task is to isolate the solver FPE by comparing the generated case against the official unpatched tutorial run, then testing whether the failure is caused by runtime parallelism, local Open MPI oversubscription, turbulence initialization, or another case-state issue.

## Next Debug Steps

1. Run the official tutorial `Allrun` in an isolated scratch directory without repository patching.
2. If official `Allrun` passes, diff generated dictionaries and processor layouts against this repository's generated case.
3. If official `Allrun` also fails, test a lower processor count or a serial/debug variant and record the OpenFOAM.com v2112/local-WSL limitation.
4. Add a targeted C07 runtime debug config rather than changing validation thresholds to mask the solver FPE.
