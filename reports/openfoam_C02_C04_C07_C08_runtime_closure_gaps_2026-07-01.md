# OpenFOAM C02/C04/C07/C08 runtime closure gaps

日期：2026-07-01

## 结论

本轮补齐的是能力卡继续推进所需的 contract、validation guard、配置入口和 replay 边界，不提升任何未满足科学证据要求的 `benchmark_status`。

## C02 potentialFoam cylinder

- 当前状态：`runtime_smoke_failed`，analytical velocity/Cp gates 未通过。
- 已补齐：`postprocess.sample_policy` 与 `error_norm_policy`，明确 field mask、finite-domain sampling、surface Cp owner-cell proxy 与误差范数。
- 仍未闭环：finite-domain reference correction、surface-native Cp 或独立 reference、baseline vs mesh_refined error trend。

## C04 motorBike RANS snappy

- 当前状态：package skeleton + dry-run contract。
- 已补齐：`runtime_smoke_wsl_v2112.yaml`，独立于 baseline dry-run，绑定 `openfoam_com_v2112`，gate 为 `smoke`。
- 仍未闭环：真实 snappyHexMesh/checkMesh/simpleFoam/forceCoeffs/yPlus runtime evidence。

## C07 conjugate heat transfer

- 当前状态：已有短时 multi-region runtime smoke，但 heat-flux 仍是 Python proxy。
- 已补齐：`postprocess.heat_flux_validation` 与 promotion guard。`targeted-regression` 及以上必须具备 native/reference heat flux 和 energy balance。
- 仍未闭环：steady convergence、native interface heat flux conservation、区域能量平衡、独立 reference。

## C08 forwardStep shock

- 当前状态：reduced-CFL runtime smoke 通过 shock sanity 与 owner-cell flux proxy。
- 已补齐：`cfl_reduced.yaml` 登记当前 smoke 的 accepted baseline samples；validation 对 promotion gate 强制要求 shock reference targets 与 native/face-flux parity。
- 仍未闭环：外部/独立 reference shock target、native `rhoPhi/phi` 或 face-field integration 与 Python proxy parity。

## 下一步执行顺序

1. 运行 C04 first runtime smoke，生成 snappy/checkMesh/simpleFoam/forceCoeffs/yPlus evidence。
2. 对 C05 做 mesh/time-step sensitivity，而不是调整 Strouhal target。
3. 对 C02 做 finite-domain correction 与 mesh_refined 趋势重跑。
4. 对 C08 增加 native/face flux parity，再引入独立 shock reference。
5. 对 C07 增加 steady run、native patch heat flux 和能量平衡。
