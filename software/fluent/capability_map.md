# Fluent Capability Map C01-C08

本文记录 Fluent 首批能力种子。它不是 tutorial zip 清单，而是把官方教程、verification manual、Workbench 教程和 legacy 素材转化为可复用能力资产的路线图。

## 来源分层

| 来源层 | 本地逻辑路径 | 角色 | 当前结论 |
| --- | --- | --- | --- |
| Fluent Tutorial Guide 2025 R1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Tutorial_Package` | 官方 tutorial case package，适合 runtime smoke 和 workflow learning | 75 个 zip，包含 `.msh/.msh.h5/.cas/.cas.h5/.dat/.dat.h5/.dsco` 等入口 |
| Fluent Workbench Tutorial Guide 2025 R1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Workbench_Tutorial_Package` | Workbench problem-definition 和参数化链路 | 3 个 zip，适合 Workbench integration seed |
| Fluid Dynamics Verification Manual | `AgentKnowledge/case_library/fluent/cases/official_tutorials/ansys_fluid_dynamics_verification_manual.pdf` | 物理 reference、解析/实验/数值验证源 | 当前未发现同名 case package；先作为 validation/reference source |
| Legacy tutorial case source | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_tutorial_case` | 旧版/辅助 tutorial case，含直接 `.cas/.dat/.msh/.jou` | 适合作为早期 standalone Fluent runtime seed |
| Legacy 2020 R2 unique | `AgentKnowledge/case_library/fluent/cases/official_tutorials/legacy_2020_r2_unique` | 去重遗留补充 | 当前仅 `single_rotating.zip`，适合旋转机械补充 |

## C01-C08 种子能力

| 编号 | capability slug | 首批角色 | 首选来源 | 验证重点 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| C01 | `steady_internal_flow_runtime` | 最小 Fluent batch/runtime 基线 | `Fluent_tutorial_case/ch07/elbow` 或 `nozzle` | case/data 读取、残差、质量守恒、压降、report export | `runtime_smoke_passed` |
| C02 | `verification_reference_validation` | verification/manual reference gate | `ansys_fluid_dynamics_verification_manual.pdf` VMFL005 | 解析式压降、量纲一致性、同构性声明 | `package_skeleton_created` |
| C03 | `mesh_convergence_trend` | 网格/迭代/参数扰动趋势 | `fluent_adaptation.zip` 或 C01 派生网格扰动 | residual trend、mesh adaptation、网格敏感性 | `benchmark_candidate` |
| C04 | `external_aero_force_coefficients` | 外流气动和力系数 | `fluent_aero_tutorial.zip`，含 reference CSV | Cd/Cl/Cp、AoA 或截面压力趋势、reference-data 对齐 | `benchmark_candidate` |
| C05 | `vof_free_surface_transient` | VOF/free surface 瞬态 | `vof.zip`、legacy `ch10/dambreak` 或 tank flush | 体积分数有界性、界面位置、质量守恒、时间步/Courant | `benchmark_candidate` |
| C06 | `sliding_rotating_mesh` | 旋转/滑移/运动网格 | `sliding_mesh.zip`、`legacy_2020_r2_unique/single_rotating.zip` | moving zone、periodic/rotating interface、时序输出 | `benchmark_candidate` |
| C07 | `heat_transfer_energy_balance` | 换热/CHT/能量平衡 | `2d_heat_exchanger_optimizer.zip`、`effusion_cooling.zip`、battery thermal cases | 温度范围、热流、能量平衡、材料/边界一致性 | `benchmark_candidate` |
| C08 | `workbench_parameter_integration` | Workbench/参数化工程链路 | `workbench_parameter.zip`、`workbench_elbow.zip` | Workbench project import、Design Point、参数和结果回传 | `benchmark_candidate` |

## 静态契约

本轮新增一个总配置 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml`，把 C01-C08 作为一个 Fluent 首批 seed suite 管理。它不是 runtime 配置，也不调用 Fluent；它只验证以下事实已经蒸馏成稳定资产：

- 每个 seed 都声明 problem definition、governing model、BC/IC、mesh/discretization、solver setup、input parameters、output quantities、benchmark source、validation criteria、perturbation axes、risks。
- 每个 seed 都保留 `benchmark_candidate`，不把 tutorial replay 或本地 dry-run 提升为数值验证。
- 每个 seed 都有 `self_generated`、`official_replay`、`comparison` 三条后续学习路径。
- runtime profile 只记录可配置边界；本机 executable 路径必须通过本地环境变量或被忽略的 machine profile 注入。

## C01 runtime smoke

C01 已新增 `configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml`、`schemas/fluent_C01_steady_internal_flow_runtime.schema.json` 与 `src/science_capability_registry/fluent/steady_internal_flow_runtime/`。本机 Fluent 2025 R1/v251 已完成一次 headless batch smoke：

- 读取 legacy `ch07/elbow` case/data。
- 使用 `2ddp -g -t1` 执行 bounded iteration。
- 对旧 case 中失效的 report-client 路径显式回答 deactivate。
- 解析 residual 与 mass-flow report，质量不平衡分数为 `7.48734375254824e-06`。
- 写出 case/data runtime artifact 到 `_results/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke/`。

该证据只证明 C01 runtime envelope 和 transcript parser；不声明 pressure-drop validation、verification-manual benchmark validation 或 mesh/refinement benchmark。

## C02 reference contract

C02 已选择 `VMFL005: Poiseuille Flow in a Pipe` 作为第一道 verification reference gate。当前配置复算 Hagen-Poiseuille 压降 `10.24 Pa`，记录手册 Fluent 表格值 `10.22 Pa`，并明确当前本地 source library 未发现 `poiseuille-flow.cas` runnable payload。

该证据只证明 reference 已经进入 config/schema/package/report 闭环；不声明 Fluent 已运行 VMFL005，也不声明 C02 已 benchmark validated。下一步应生成轴对称管流 Fluent case，并用三档网格验证压降误差趋势。

## Official replay manifest

新增 `configs/fluent/official_replay_manifest/c01_c08_sources.yaml`，用于统一登记 C01-C08 的官方/legacy/Workbench/reference 来源绑定。一次本地只读扫描结果为 9 个来源包、24 个 source entries、8 个 capability bindings，且 expected entry classes 无缺失。

该 manifest 把 C05/C06 明确标记为 mesh-only setup seed，把 C08 标记为 Workbench project seed，防止后续误把 mesh 或 `.wbpz` 当成 standalone Fluent batch 输入。

## 自生成 vs 官方 replay 学习闭环

每个 seed 都应最终支持两条路径：

1. `self_generated`：由 config 生成 Fluent journal 或 case setup，运行并提取 canonical metrics。
2. `official_replay`：解压官方 zip，识别入口文件，运行 Fluent 或 Workbench replay，提取同一套 canonical metrics。

对比结果必须分类为 geometry/mesh/model/boundary/unit/initialization/runtime-profile/reference mismatch，而不是简单调阈值到通过。

## 当前不声明

- 不声明任一 Fluent seed 已完成 solver runtime。
- 不声明 tutorial case 等于 verification benchmark。
- 不声明 Workbench package 可 headless 自动化；需要单独 runtime profile。
- 不提交大型解压内容或求解输出；runtime evidence 只进入 `_results/fluent/`，稳定总结进入 `reports/`。
