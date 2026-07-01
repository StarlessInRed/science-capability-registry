# OpenFOAM C05 v2412 native forceCoeffs Strouhal diagnostic - 2026-07-01

## Scope

- capability: `C05_transient_cylinder_vortex_shedding`
- runtime profile: `openfoam_com_v2412`
- smoke config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_smoke_wsl_v2412.yaml`
- long-horizon config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_wsl_v2412.yaml`
- smoke result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_smoke_wsl_v2412`
- long-horizon result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_wsl_v2412`

## Native forceCoeffs smoke

The v2412 short smoke closes the local v2112 native `forceCoeffs` blocker for this host:

- `./Allrun.pre`: returncode `0`
- `pimpleFoam`: returncode `0`
- final time: `0.19983004`
- max Courant: `0.4933629867730658`
- native source: `openfoam_forceCoeffs`
- coefficient rows: `201`
- validation: `passed=true`

The parser was corrected for OpenFOAM.com v2412 `coefficient.dat` columns (`Time Cd ... Cl ... CmPitch ...`). The old `Time Cm Cd Cl` assumption incorrectly mapped `Cd(f)` into `Cl`.

## Native Strouhal attempt

The v2412 long-horizon native run completed, but the integration gate remains failed:

- final time: `7.999830037232331`
- max Courant: `0.4933629867730658`
- coefficient rows: `8001`
- force source: `openfoam_forceCoeffs`
- FFT Strouhal: `0.13999999999997398`
- target range: `[0.16, 0.24]`
- failed check: `postprocess.strouhal_target_range`

Native `Cl` contains small high-frequency local peaks, so this config uses `lift_fft` as the primary frequency estimate. The native FFT result agrees with the previous v2112 Python patch-surface proxy FFT result (`St~0.14`), which means the previous low Strouhal result is not explained by the Python proxy alone.

## Status

C05 remains `validation_failed`. The current blocker is now narrower:

- v2112 native forceCoeffs is blocked by local `sha1` functionObject IO behavior.
- v2412 native forceCoeffs works and produces finite coefficient series.
- both native v2412 FFT and v2112 Python proxy indicate `St~0.14`, below the configured target.

Benchmark promotion still requires an evidence-backed reference policy for this official `cylinder2D` setup plus mesh/time-step sensitivity or another independent shedding-frequency reference.
