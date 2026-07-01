# OpenFOAM C01-C08 能力路线闭环报告

## 结论

本轮多 agent 审计后，OpenFOAM 首批能力的下一阶段主线不是继续扩展新 capability，而是把 C01-C08 从“单点 runner/报告”收敛为“可调度、可复验、可审计”的能力资产链。

本轮已经完成的闭环：

- `configs/registry/capability_catalog.json` 增加 `dispatch_status`、`current_gate`、`primary_evidence_id`、`runtime_profile_path`、`benchmark_manifest_path` 和统一 `result_contract`。
- `schemas/capability_registry.schema.json` 强制 catalog 暴露调度状态和结果合同，避免消费者把 `package_skeleton_created` 或 `validation_failed` 当作可生产调用能力。
- `schemas/openfoam_runtime_evidence_manifest.schema.json` 和 `src/science_capability_registry/openfoam/evidence_contract.py` 建立 OpenFOAM runtime evidence envelope，不改变各 Cxx 的物理 metrics 结构。
- C08 catalog 已引用最新通过的 `openfoam_C08_cfl_reduced_runtime_smoke_2026-07-01`，但 `benchmark_status` 保持 `package_skeleton_created`，因为缺 reference shock targets 和 native flux parity。
- `science-intelligence-gateway`、`agent-workflow-registry`、`Sci_AI_OS` 已增加只读 `capability_catalog_ref` 合同。消费者只引用 SCR catalog/evidence，不复制 OpenFOAM 科学事实。

## 当前状态

| 能力 | 当前状态 | 本轮调度判断 | 下一闭环 |
| --- | --- | --- | --- |
| C01 lid-driven cavity | `benchmark_validated` | `replay_ready` | 补 Ghia 或等价中心线参考，进入 double-v |
| C02 potential flow cylinder | `package_skeleton_created` | `runtime_smoke_failed` | 修正有限域采样、Cp/速度误差和 mesh-refinement 趋势 |
| C03 backward-facing step | `benchmark_validated` | `replay_ready` | 补 native wallShear/yPlus parity 和外部 RANS reference |
| C04 motorBike RANS snappy | `package_skeleton_created` | `static_ready` | 跑通 snappyHexMesh/checkMesh/simpleFoam、forceCoeffs、y+ |
| C05 transient cylinder | `validation_failed` | `validation_failed` | 先修 Strouhal：native/DMD/reference parity，再做 mesh/time-step sensitivity |
| C06 dam break VOF | `benchmark_validated` | `replay_ready` | 补 full-horizon、native sampling parity、外部 dam-break reference |
| C07 CHT cooling | `benchmark_candidate` | `integration_evidence_ready` | MHR 长时稳态、native/reference heat-flux、能量平衡 |
| C08 forward-step shock | `package_skeleton_created` | `runtime_smoke_passed` | 配置 shock 位置/压力/密度参考和 native flux parity |

## 十条工作路线

1. **能力目录与证据一致性收敛**  
   本轮已完成 catalog 调度字段、主证据字段和结果合同。后续 gate 应检查 asset card、catalog、evidence index、examples index 是否一致。

2. **统一 evidence manifest 与 report contract**  
   本轮已新增 OpenFOAM runtime evidence envelope schema/helper。后续逐步让 C01-C08 runner 在 dry-run/runtime 后调用 `validate_evidence_manifest()`。

3. **OpenFOAM runtime profile 调度层**  
   本轮 catalog 暴露 `runtime_profile_path`。后续 Science AI OS 或 gateway 调用前，应先读取该 profile，而不是从 solver 名或路径猜测 runtime。

4. **C08 shock smoke 晋级 benchmark**  
   当前 reduced-CFL smoke 已通过，但只证明 solver health 和 shock sanity。晋级必须补 configured shock reference、压力/密度跳跃参考和 native/face-field flux parity。

5. **C07 CHT 热流闭环**  
   当前 MHR integration matrix 通过，但仍是短时和 Python heat-flux proxy。下一步是稳态收敛、interface heat-flux conservation 和 energy balance。

6. **C05 Strouhal 失败恢复**  
   当前 long-horizon run 失败在 Strouhal gate，不能放宽阈值掩盖问题。下一步需要 DMD、native forceCoeffs 或独立 reference parity。

7. **C02 potentialFlow 解析验证闭环**  
   当前 runtime 可执行但 analytical gate 失败。下一步先确认采样位置、有限域误差和 Cp 定义，再谈 benchmark 晋级。

8. **C04 motorBike 首次 runtime 闭环**  
   当前只有 static readiness。下一步目标是 mesh quality、simpleFoam completion、Cd/Cl tail-window 和 y+ artifact。

9. **C01/C03/C06 frozen benchmark replay**  
   三个已 validated 能力应优先变成 replay benchmark，而不是继续改 runner。下一步补 replay command、artifact hash、外部 reference 或 double-v 报告。

10. **v2412 / cross-profile targeted regression**  
    当前主要证据来自 OpenFOAM.com v2112 WSL。下一步用 v2412 或另一 runtime profile 对 C01/C03/C06 做 targeted regression，分类版本差异。

## 跨仓库边界

- `science-capability-registry` 是 OpenFOAM capability catalog 和 evidence index 正源。
- `science-intelligence-gateway` 只产生 `capability_catalog_ref` 候选引用和 review 标记，不直接写 SCR。
- `agent-workflow-registry` 只记录 source intelligence 的 routing/handoff，不登记 OpenFOAM 能力本体。
- `Sci_AI_OS` 只消费 catalog ref、evidence manifest 和 frozen benchmark，用于 execution/replay/scientific CI。

## 验收口径

本轮验收属于 `static-readiness` 到 `targeted-regression` 范围：

- registry catalog/schema/helper 测试通过。
- Sci_AI OS OpenFOAM evidence 和 scientific CI 单测通过。
- gateway `SOURCE_RECORD` 的 `capability_catalog_ref` fail-fast 检查通过。
- JSON schema 与示例解析、Sci AI OS 示例 schema 校验通过。

未完成且不能声明完成的内容：

- 没有重跑 C02/C04/C05/C07/C08 的真实 OpenFOAM 长 runtime。
- 没有晋级任何 `benchmark_status`。
- 没有把 `_results/` 运行产物提交为仓库资产。
