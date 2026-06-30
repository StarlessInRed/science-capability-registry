# OpenFOAM C07 official cpuCabinet runtime debug - 2026-06-30

## Scope

This report closes the current C07 runtime-debug loop for the local OpenFOAM.com v2112 cpuCabinet CHT capability. It compares the package-generated runtime failure with official tutorial baselines under the same WSL host.

Runtime profile:

- OpenFOAM distribution: OpenFOAM.com v2112
- WSL distro: Ubuntu-24.04
- Solver: `chtMultiRegionSimpleFoam`
- Tutorial: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/cpuCabinet`

## Runs

### 1. Generated package runtime smoke

Evidence path:

- `_results/openfoam/conjugate_heat_transfer_cooling/runtime_smoke_wsl_v2112/`
- committed summary: `reports/openfoam_C07_conjugate_heat_transfer_cooling_runtime_smoke_attempt_2026-06-30.md`

Result:

- Mesh/preprocess/checkMesh completed.
- `mpirun --oversubscribe -np 10 chtMultiRegionSimpleFoam -parallel` reached `Time = 2`.
- Solver failed with a true floating point exception in `compressibleTurbulenceModel::phi()` / `realizableKE::correct()`.

### 2. Official unmodified `Allrun`

Evidence path:

- `_results/openfoam/conjugate_heat_transfer_cooling/official_cpuCabinet_allrun_wsl_v2112_20260630_114248/`

Result:

- Top-level `Allrun` returned `0`, but the parallel logs show the solver did not actually run.
- `log.splitMeshRegions`, `log.topoSet`, and `log.chtMultiRegionSimpleFoam` report Open MPI "not enough slots" for 10 requested processes.
- This run is a local launcher/setup failure, not solver validation evidence.

### 3. Official unmodified case with explicit `--oversubscribe`

Evidence path:

- `_results/openfoam/conjugate_heat_transfer_cooling/official_cpuCabinet_oversubscribe_wsl_v2112_20260630_114714/`

Result:

- `blockMesh`, `surfaceFeatureExtract`, `snappyHexMesh`, `decomposePar`, `restore0Dir`, `splitMeshRegions`, and `topoSet` completed with return code `0`.
- `chtMultiRegionSimpleFoam` failed before useful time advancement with OpenFOAM v2112 `sha1` IO fatal errors.
- This matches the known local OpenFOAM.com v2112 WSL functionObject/sha1 behavior observed in other capabilities.

### 4. Official case with only probe/sha1 mitigation and short horizon

Evidence path:

- `_results/openfoam/conjugate_heat_transfer_cooling/official_cpuCabinet_probe_removed_short_wsl_v2112_20260630_115130/`

Controlled differences from the official tutorial:

- removed the `functions { #include "probes" }` block to bypass local `sha1` IO fatal errors;
- set `endTime` to `5` and `writeInterval` to `1` to keep the diagnostic bounded;
- used `mpirun --oversubscribe -np 10` for parallel commands.

Result:

- Mesh and region split pipeline completed.
- Solver reached `Time = 2`.
- `chtMultiRegionSimpleFoam` exited with return code `136`.
- Log signatures show `Signal: Floating point exception (8)` and stack traces through `compressibleTurbulenceModel::phi()` and `RASModels::realizableKE::correct()`.

## Conclusion

The current C07 blocker is not explained by the package runner's material, heat-source, MRF, or decomposition patches alone. A near-official cpuCabinet run, after only the required local `sha1` probe mitigation and MPI oversubscription, reproduces the same early `Time = 2` floating point exception in the same turbulence-model path.

Keep `benchmark_status: benchmark_candidate`. C07 has a working dry-run/package path and reproducible runtime-failure evidence, but no validated CHT solver baseline, region temperature metrics, interface balance metrics, or perturbation matrix.

## Next technical direction

1. Add a dedicated C07 diagnostic config that switches the fluid turbulence closure away from `realizableKE` where supported by the v2112 tutorial dictionaries.
2. Test a reduced serial or lower-rank decomposition path to separate parallel decomposition sensitivity from turbulence-model failure.
3. If cpuCabinet remains unstable on v2112, pivot C07 validation to another OpenFOAM.com v2112 CHT tutorial with explicit solid/fluid regions, then keep cpuCabinet as a known failing benchmark candidate.
