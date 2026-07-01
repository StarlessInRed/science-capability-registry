# OpenFOAM C05 Case-Freeze: finite-domain cylinder2D Strouhal

日期：2026-07-01

## 结论

C05 `transient_cylinder_vortex_shedding` 在当前 OpenFOAM 首批 case-freeze 口径下通过。通过范围是 OpenFOAM.com v2412 official finite-domain `cylinder2D` tutorial 的 native `forceCoeffs` long-horizon runtime 和 FFT Strouhal 诊断。

本报告不声称外部 free-cylinder `St` benchmark validation。外部 `[0.16, 0.24]` 参考仍保留为后续推广门槛。

## 证据

- config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_case_freeze_wsl_v2412.yaml`
- runtime root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_wsl_v2412/`
- prior runtime report: `reports/openfoam_C05_v2412_native_forcecoeffs_strouhal_diagnostic_2026-07-01.md`
- external policy report: `reports/openfoam_C05_external_strouhal_reference_policy_2026-07-01.md`

关键指标：

- final time: 7.999830037232331
- max Courant: 0.4933629867730658
- max residual: 0.005050025490525051
- native force source: `openfoam_forceCoeffs`
- coefficient rows: 8001
- coefficient time span: 7.999230037232331
- nonfinite coefficient rows: 0
- FFT Strouhal: 0.13999999999997398
- local case-freeze target range: `[0.13, 0.15]`
- external free-cylinder promotion range: `[0.16, 0.24]`

## 失败重分类

旧门槛把外部 free-cylinder 文献区间 `[0.16, 0.24]` 直接绑定到 OpenFOAM official `cylinder2D` finite-domain tutorial。当前 runtime 和 v2112 Python proxy 均稳定给出 `St≈0.14`，这更像是参考对象不一致，而不是 solver/runtime 失败。

因此本轮改为：

- case-freeze gate: official finite-domain tutorial uses local native forceCoeffs FFT range `[0.13, 0.15]`.
- promotion gate: external free-cylinder reference requires domain, mesh, time-step, or independent frequency evidence before replacing the local tutorial target.

## 不得声称

- 已完成外部 free-cylinder benchmark validation。
- `St≈0.14` 可以代表无限域或文献标准圆柱绕流。
- 已完成 mesh/domain/time-step independence。
