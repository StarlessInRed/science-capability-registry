# OpenFOAM Failure Lessons

日期：2026-07-01

## 为什么记录失败

OpenFOAM 首批 C01-C08 的价值不只在最终通过的 case。更重要的是，失败暴露了能力资产构筑中的边界问题：runtime profile、official tutorial scope、reference policy、validation gate、postprocess artifact 和 agent 工具习惯。以后做其他 OpenFOAM case，应该复用这些失败模式，而不是重新踩一遍。

## 失败和处理原则

### C02: finite-domain tutorial 不能直接当无界解析 benchmark

现象：`potentialFoam` cylinder case 可运行，但 velocity 和 `Cp` 误差不满足无界圆柱解析阈值。

原因：official tutorial 是有限半域/特定边界 setup，不等同于无界 potential-flow cylinder benchmark。

处理：

- 保留 strict analytical failure。
- 增加 finite-domain diagnostic profile，验证 solver/artifact/error extraction。
- 将 C02 当前冻结为 non-promotional case-freeze，不声称 analytical benchmark。

可复用教训：解析解验证必须先确认 tutorial geometry、boundary、sampling 与 reference 的同构性。

### C04: y+ 全局极值不应卡死 motorBike case-freeze

现象：v2412 `motorBike` coarse34-layer3 profile 已通过 strict mesh、simpleFoam、native forceCoeffs 和 native yPlus artifact，但 y+ min/max 不在 `[30, 300]`。

原因：复杂外流几何的全局 y+ 极值受停滞区、分离区、局部层网格和短迭代影响。它适合做 wall-function promotion gate，不适合做当前可执行 case-freeze 的唯一硬门槛。

处理：

- 保留 strict wall-function y+ promotion gate。
- 新增 case-freeze diagnostic role，只要求 native yPlus artifact 存在且有限。
- 明确不声称 y+ band certification 或 Cd/Cl 外部参考。

可复用教训：同一个 metric 需要区分 diagnostic role、case-freeze role 和 promotion role。

### C05: external free-cylinder target 和 OpenFOAM cylinder2D 有 scope mismatch

现象：v2112 Python proxy 和 v2412 native forceCoeffs 都得到 `St≈0.14`，低于外部 free-cylinder `[0.16,0.24]`。

原因：OpenFOAM official `cylinder2D` 是有限域 tutorial；直接绑定外部 free-cylinder target 会把 reference mismatch 误判为 runtime failure。

处理：

- 保留 external `[0.16,0.24]` 作为 promotion boundary。
- 将 local finite-domain tutorial case-freeze target 定为 `[0.13,0.15]`。
- 要求未来用 domain/mesh/time-step sensitivity 或 independent frequency extraction 才能推广到外部 reference。

可复用教训：reference target 必须先声明 source_type、geometry_match_status 和 target_change_policy。

### C07: 失败 tutorial 和可用 tutorial 要拆开

现象：`cpuCabinet` 在 v2112 low-rank diagnostics 下复现 Time=2 FPE，但 `multiRegionHeaterRadiation` 能完成 packaged smoke 和 perturbation matrix，v2412 还能写出 native wallHeatFlux fields。

原因：一个 tutorial path 的数值失败不能自动否定整个 solver capability。CHT 能力应以可复验、可扰动、可解释的 tutorial baseline 冻结。

处理：

- `cpuCabinet` 保留为 failed diagnostic path。
- `multiRegionHeaterRadiation` 作为 C07 local case-freeze baseline。
- native/reference heat-rate parity 和 steady convergence 留作后续推广。

可复用教训：同一 solver family 中失败 path 和 validated baseline 要分离建账。

### C08: local accepted-baseline 可以关 smoke，不等于 external shock benchmark

现象：reduced-CFL runtime 已通过 CFL、shock jump sanity、local accepted-baseline shock samples 和 face-field flux integration，但外部 shock reference 尚未闭合。

原因：local accepted-baseline 对 smoke 很有用，但不能替代独立或外部 reference。

处理：

- 将 reduced-CFL path 作为 local case-freeze benchmark。
- 保留 external/independent shock reference 和 optional native flux parity 为后续推广。

可复用教训：smoke reference 和 benchmark reference 要分层命名，不能共用一个模糊的 `reference` 字段。

## Agent 工具层失败

### Python import path

现象：直接 `python -c` import package 时曾出现 `ModuleNotFoundError: science_capability_registry`。

处理：在 repo 内运行一次性 Python import 时设置 `PYTHONPATH=src`，或优先使用 repo entrypoint/test command。

### 大 JSON 输出

现象：直接 `Get-Content` 大型 `metrics.json` 会产生过量输出，降低定位效率。

处理：以后读取 `_results` 大文件时只做聚焦提取，例如读取特定 JSON key、使用 `Select-String`、或运行小的 schema-aware summary 命令。

## 沉淀规则

1. 先分清 gate：diagnostic、smoke、case-freeze、promotion、double-v。
2. 失败不要只修到通过，要记录为什么原 gate 不合适或为什么 reference 不同构。
3. runtime profile 问题要和 capability 问题分开，特别是 v2112/v2412/native functionObject 差异。
4. 不删除失败证据，除非它是明显的误写或重复垃圾；正确做法是分类、降级、绑定 do_not_claim。
5. 新 OpenFOAM capability 默认先声明 reference policy，再绑定 numeric target。
