# OpenFOAM C08 face-field flux parity evidence - 2026-07-01

## 范围

本报告记录 C08 `compressible_shock_capturing_forward_step` 在 reduced-CFL runtime 上新增的 face-field flux integration 证据。

- config: `configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml`
- result root: `_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced/`
- artifact: `postprocess/face_flux_parity_summary.csv`
- gate: `smoke`
- status: `passed`

## Flux parity metrics

Face-field integration 使用 final-time boundaryField 值；当 patch 只有 gradient/value 不可直接读取时，显式记录 owner-cell fallback。

- method: `face_field_integration`
- included patches: `inlet`, `outlet`, `bottom`, `top`, `obstacle`
- boundaryField value sources: `8`
- owner-cell fallback sources: `12`
- mass imbalance: `0.025244076037939014`
- total-energy imbalance: `0.011272779328549172`

这些值与 owner-cell proxy 同阶且接近：

- owner-cell mass imbalance proxy: `0.025242669026375803`
- owner-cell total-energy imbalance proxy: `0.011272417945887505`

## 状态结论

C08 现在不再只有 owner-cell proxy；它还有独立的 final-time face-field integration artifact。该证据足以关闭 smoke 层面的 face-field parity artifact gap。

但它仍不是 native OpenFOAM `rhoPhi/phi` functionObject parity，也不是外部 shock benchmark。C08 benchmark promotion 仍需要外部或独立审阅的 shock position / pressure jump / density jump reference。
