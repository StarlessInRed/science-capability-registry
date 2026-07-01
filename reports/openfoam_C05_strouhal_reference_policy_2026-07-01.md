# OpenFOAM C05 Strouhal reference policy - 2026-07-01

## Scope

本报告记录 C05 `transient_cylinder_vortex_shedding` 的 Strouhal 目标闭环策略。它不是一次新的 benchmark promotion，而是防止用阈值迁就当前本地结果的 reference policy。

- capability: `C05_transient_cylinder_vortex_shedding`
- current asset status: `validation_failed`
- current failed gate: `integration`
- relevant runtime evidence:
  - `_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112_20260630_003/`
  - `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_wsl_v2412/`

## Observed State

Both available long-horizon paths give a low shedding frequency:

- v2112 Python patch-surface proxy FFT Strouhal: about `0.14`
- v2412 native forceCoeffs FFT Strouhal: about `0.14`
- configured target range: `[0.16, 0.24]`

The v2412 native forceCoeffs run rules out the simplest explanation that the low value is only caused by the Python proxy. It does not prove the configured target is wrong.

## Policy

Do not change the Strouhal target range until one of these reference sources is selected and recorded in config-visible form:

- external benchmark or literature source for the exact official `cylinder2D` setup
- official OpenFOAM tutorial reference with geometry, Reynolds number, and force signal definition
- independently reviewed frequency extraction from the existing native force signal
- independent numerical method such as DMD or a second solver/profile, followed by mesh/time-step sensitivity

The selected policy must state:

- reference provenance and `source_type`
- target range and tolerance
- force source accepted for validation
- frequency method accepted for validation
- required mesh/time-step sensitivity before `benchmark_validated`

## Next Acceptance Checks

- Add config-visible `strouhal_reference_policy` or equivalent schema fields before changing thresholds.
- Keep v2112 native forceCoeffs marked as a local profile limitation unless the sha1 IO blocker is fixed.
- Require native v2412 forceCoeffs, DMD, or independent frequency parity.
- Require at least one mesh/time-step sensitivity case before benchmark promotion.

C05 remains `validation_failed`.
