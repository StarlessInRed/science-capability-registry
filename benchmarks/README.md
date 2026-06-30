# Benchmarks

`benchmarks/` 是 `science-capability-registry` 中的 frozen scientific benchmark 索引。

本目录只保存科学验证问题的 canonical definition、reference metrics、artifact hash 和 validation criteria。它不执行 solver，不保存大体量 runtime output，也不定义 workflow。实际 evidence replay、regression comparison 和 memory update 由 `Sci_AI_OS` 执行。

## 当前冻结基准

| Benchmark ID | Solver | Capability binding | Status | Sci_AI_OS replay |
| --- | --- | --- | --- | --- |
| `openfoam_c01_lid_driven_cavity` | OpenFOAM | `cfd.openfoam.lid_driven_cavity_incompressible_laminar` | `frozen_canonical` | `scientific_ci_openfoam_c01` |
| `openfoam_c03_backward_facing_step_rans_internal_flow` | OpenFOAM | `cfd.openfoam.backward_facing_step_rans_internal_flow` | `frozen_canonical` | `scientific_ci_openfoam_c03` |
| `openfoam_c06_dam_break_vof_free_surface` | OpenFOAM | `cfd.openfoam.dam_break_vof_free_surface` | `frozen_canonical` | `scientific_ci_openfoam_c06` |
| `cantera_c01_constant_pressure_ignition` | Cantera | `combustion.cantera.constant_pressure_ignition` | `frozen_canonical` | `scientific_ci_cantera_c01` |

## 目录契约

每个 benchmark 子目录至少应包含：

- `benchmark_manifest.json`：benchmark 的主入口，声明 benchmark id、capability binding、solver、状态和下游 replay 语义。
- `expected_metrics.json`：可比较的数值指标和允许阈值。
- `validation_criteria.json`：PASS / FAIL / PARTIAL 的判定规则。
- `artifact_hash.json`：冻结参考文件的完整性约束。

按 benchmark 类型可增加：

- `residual_reference.json`：OpenFOAM 等迭代求解器的 residual reference。
- `postprocess_reference/`：速度剖面、压力场、点火延迟、温度曲线等后处理 reference。
- `reference_case/`：可提交的小体量参考输入；真实大体量运行产物不得进入 Git。

## 边界规则

- `science-capability-registry` 是 benchmark truth source，只定义科学基准。
- `Sci_AI_OS` 读取本目录，执行 evidence replay 和 regression validation。
- `science-intelligence-gateway` 只产生 routing decision 和 Skill spec，不读取本目录做 solver validation。
- `agent-workflow-registry` 只保存 parsing / ingestion / tool workflow，不保存 benchmark truth。

## 新增 benchmark 规则

新增 benchmark 时必须同时满足：

- 有明确 capability binding。
- 有可追溯的 source 或 real execution evidence。
- 有最小可比较 metrics。
- 有 validation criteria。
- 不提交大体量 solver output、临时 runtime 目录或本机绝对路径。
- 更新本索引表，使 benchmark 可发现。
