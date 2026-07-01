# OpenFOAM C01-C08 暂停收敛结论

日期：2026-07-01  
范围：OpenFOAM 首批能力地图 C01-C08。仓库实际编号从 C01 开始，用户口径中的 C0-C8 在本报告中按 C01-C08 处理。

## 结论

OpenFOAM 可以在本轮以 `registry_pause_closure` 口径暂时收敛并放下，但不能声明 C01-C08 已全部完成科学 benchmark 收敛或 double-v 收敛。

本轮可成立的收敛定义是：

- 每个 C01-C08 都已有 capability map、catalog 状态、evidence index 或 failure ledger 边界。
- 已通过的本地 integration/smoke 证据和未通过的科学验证边界被分开记录。
- 仍未完成的项目有明确 priority、failure_id、owner_next_action 和 `do_not_claim` 边界。
- 后续恢复 OpenFOAM 时可以直接从 `reports/openfoam_failure_ledger.yaml` 的 `work_queue` 接续，而不是依赖对话记忆。

## 当前状态

| 编号 | 当前 registry 状态 | 本轮暂停结论 | 不能声明 |
| --- | --- | --- | --- |
| C01 | `benchmark_validated`，integration | 可作为 registry-local integration 能力暂时放下。 | 外部中心线 benchmark、mesh/time double-v 已完成。 |
| C02 | `package_skeleton_created`，runtime smoke 失败 | 有 runnable path 和 finite-domain diagnostic，但严格无界圆柱解析门槛未过，暂停为 P1 active failure。 | 无界圆柱解析 benchmark、surface Cp 验证、`benchmark_validated`。 |
| C03 | `benchmark_validated`，integration | 可作为 registry-local integration 能力暂时放下。 | native wallShearStress/yPlus parity、外部 RANS reference、double-v。 |
| C04 | `package_skeleton_created`，smoke | strict mesh、20-step solver、native forceCoeffs 已过；y+ wall-function 范围未过，暂停为 P0 active failure。 | 外流气动 benchmark、Cd/Cl reference closure、native y+ validation。 |
| C05 | `validation_failed`，integration | long-horizon 和 v2412 native forceCoeffs 已有，Strouhal 仍低于目标区间，暂停为 P0 active failure。 | Strouhal benchmark pass、阈值放宽、`benchmark_validated`。 |
| C06 | `benchmark_validated`，integration | 可作为 registry-local short-horizon/free-surface integration 能力暂时放下；v2412 sampling/full-horizon 证据已增强。 | 外部 dam-break benchmark、sampleSets value parity、double-v。 |
| C07 | `benchmark_candidate`，integration evidence ready | MHR integration matrix 和 v2412 native wallHeatFlux field-generation 只能作为缓解证据，暂停为 P1/P2 heat-flux parity gap。 | native heat-flux conservation、steady CHT convergence、`benchmark_validated`。 |
| C08 | `package_skeleton_created`，smoke | reduced-CFL shock smoke 和 face-field flux evidence 已过；外部 shock reference 缺口仍在，暂停为 P1 promotion blocker。 | 外部 shock benchmark、native flux parity、`benchmark_validated`。 |

## 暂停门槛

本轮暂停 OpenFOAM 的门槛已经满足：

- C01/C03/C06 是可调度、可复测的本地 integration 能力，保留 `benchmark_validated`，但 double-v 不声明。
- C02/C04/C05/C07/C08 都没有被误 promoted；对应失败或缺口已进入 failure ledger。
- C04 和 C05 的最高优先级问题仍然是 active P0，但已经不是未分类卡点：C04 是 y+ wall-normal/layer strategy，C05 是 Strouhal sensitivity 或 independent frequency extraction。
- C02/C07/C08 的 promotion blockers 已被拆成 P1/P2 后续工作，不阻止用户切换到其他资产方向。

## 恢复入口

如果以后恢复 OpenFOAM，建议只从以下队列开始，不重新发散能力地图：

1. `OF-WQ-001`：C04 y+ wall-function closure。
2. `OF-WQ-002`：C05 Strouhal sensitivity and independent frequency closure。
3. `OF-WQ-003`：C02 finite-domain or domain-expanded analytical closure。
4. `OF-WQ-004`：C07 heat-flux parity and steady-energy closure。
5. `OF-WQ-005`：C08 external shock reference and flux parity。
6. `OF-WQ-006`：C01/C03/C06 double-v follow-up。

在转向其他科学资产前，OpenFOAM 的正确状态不是“全部完成”，而是“首批能力已完成可审计暂停收敛，未完成项已归档为可恢复工作队列”。
