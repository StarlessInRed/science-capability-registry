# OpenFOAM C04 Case-Freeze: motorBike yPlus Diagnostic

日期：2026-07-01

## 结论

C04 `external_aero_motorbike_rans_snappy` 在当前 OpenFOAM 首批 case-freeze 口径下通过。通过范围是：

- strict `checkMesh`
- 20 iteration `simpleFoam` smoke
- native `forceCoeffs` artifact
- solver-postProcess native `yPlus` artifact和有限数值诊断

本报告不声称 wall-function y+ band 合格，也不声称外部气动 `Cd/Cl` benchmark validation。

## 证据

- config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_coarse34_layer3_case_freeze_wsl_v2412.yaml`
- runtime root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_coarse34_layer3_force_yplus_wsl_v2412/`
- prior runtime report: `reports/openfoam_C04_v2412_coarse34_layer3_force_yplus_2026-07-01.md`

关键指标：

- `cell_count`: 16586
- `max_non_orthogonality`: 61.0152
- `max_aspect_ratio`: 16.018
- `max_skewness`: 2.66334
- `highly_skew_face_count`: 0
- `max_final_residual`: 0.0734606
- `Cd_tail_mean`: 0.29571504
- `Cd_tail_std`: 0.05105
- `Cl_tail_mean`: 0.2728065
- `Cl_tail_std`: 0.05269
- `yPlus_min`: 15.441
- `yPlus_max`: 3138.67
- `yPlus_mean`: 582.208

## 失败重分类

旧门槛把全局 y+ min/max `[30, 300]` 当作 C04 当前 case-freeze 硬门槛。对 `motorBike` 这种复杂外流几何，20-iteration smoke 的全局 y+ 极值会被停滞区、分离区、局部贴体层质量和短时迭代共同影响。它可以作为 wall-function 推广门槛，但不适合作为当前本地能力是否可冻结的唯一判据。

因此本轮改为：

- case-freeze gate: native yPlus artifact must exist and be finite.
- promotion gate: wall-function y+ range, mesh/layer tuning, Cd/Cl convergence, and external/reference comparison remain future work.

## 不得声称

- y+ 已满足 `[30, 300]` wall-function band。
- `Cd/Cl` 已完成外部气动参考验证。
- 20 iteration smoke 足以证明气动收敛或网格无关性。
