# OpenFOAM C07 heat-flux parity policy - 2026-07-01

## Scope

本报告记录 C07 `conjugate_heat_transfer_cooling` 的 heat-flux closure 策略。当前 multiRegionHeaterRadiation package provides integration evidence, but not benchmark-grade CHT validation.

- capability: `C07_conjugate_heat_transfer_cooling`
- current asset status: `benchmark_candidate`
- stable mitigation evidence:
  - `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112_20260630_003/`
  - `_results/openfoam/conjugate_heat_transfer_cooling/perturb_heater_temperature_high_wsl_v2112_20260630_001/`
  - `_results/openfoam/conjugate_heat_transfer_cooling/perturb_airflow_high_wsl_v2112_20260630_001/`
  - `_results/openfoam/conjugate_heat_transfer_cooling/perturb_mesh_refinement_wsl_v2112_20260630_001/`

## Current Boundary

The packaged MHR baseline and perturbation matrix pass short-horizon integration checks. However:

- the horizon is short, around `Time=2`
- heat-flux evidence is proxy or field-derived
- native `postProcess wallHeatFlux` fails on local v2112 with sha1 IO behavior
- cpuCabinet remains a known failing diagnostic path and is not the packaged baseline

## Policy

Benchmark promotion requires one of these heat-flux closures:

- native wallHeatFlux works on a selected OpenFOAM profile for all required regions
- independent face-field heat-rate integration is cross-validated against native or external reference evidence

In addition, C07 needs:

- longer steady convergence evidence
- regional energy-balance checks
- temperature range sanity
- explicit separation between cpuCabinet diagnostics and MHR package evidence

## Next Acceptance Checks

- Do not treat short-horizon proxy heat flux as native heat-flux conservation.
- Keep face-field integration as mitigation until parity is documented.
- Add a heat-flux parity config/report before asset promotion.
- Add longer steady convergence and energy balance evidence before `benchmark_validated`.
