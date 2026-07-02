# Fluent Capability Map C01-C08

本文件记录 Fluent 首批 C01-C08 科学能力资产的范围、证据来源、当前验证门槛和未闭环边界。它的目标不是把官方教程当成操作教程复述，而是把 tutorial case、verification manual、Workbench tutorial 和 legacy case source 转换为可执行、可复现、可审查的能力路线图。

## 来源分布

| 来源包 | 逻辑路径 | 证据角色 | 当前观察 |
| --- | --- | --- | --- |
| Fluent Tutorial Guide 2025 R1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Tutorial_Package` | 官方 tutorial case package；适合 runtime smoke 与 workflow learning | 75 个 zip，包含 `.msh/.msh.h5/.cas/.cas.h5/.dat/.dat.h5/.dsco` 等资源 |
| Fluent Workbench Tutorial Guide 2025 R1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Workbench_Tutorial_Package` | Workbench problem-definition 与参数工作流来源 | 3 个 zip，适合 Workbench integration seed |
| Fluid Dynamics Verification Manual | `AgentKnowledge/case_library/fluent/cases/official_tutorials/ansys_fluid_dynamics_verification_manual.pdf` | 解析解、实验值、数值验证目标来源 | 当前未发现同步 case package，因此先作为 validation/reference source |
| Legacy tutorial case source | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_tutorial_case` | 旧版 tutorial case，可直接提供 `.cas/.dat/.msh/.jou` | 适合作为早期 standalone Fluent runtime seed |
| Legacy 2020 R2 unique | `AgentKnowledge/case_library/fluent/cases/official_tutorials/legacy_2020_r2_unique` | 去重后的旧版本补充来源 | 当前包含 `single_rotating.zip`，适合旋转机械补充 |

## C01-C08 能力分解

| 编号 | capability slug | 科学/工程角色 | 首选来源 | 验证重点 | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| C01 | `steady_internal_flow_runtime` | 最小 Fluent batch/runtime 能力 | legacy `ch07/elbow` 与 `nozzle` | case/data 读取、残差、质量守恒、压降、report export | `runtime_smoke_passed` |
| C02 | `verification_reference_validation` | verification/manual reference gate | VMFL005 Poiseuille pipe | 解析压降、手册值一致性、同源 mesh-readability smoke | `runtime_mesh_smoke_passed` |
| C03 | `mesh_convergence_trend` | 网格/自适应/扰动趋势 | `fluent_adaptation.zip` 与 C01 网格扰动 | residual trend、mesh adaptation、结果单调性 | `benchmark_candidate` |
| C04 | `external_aero_force_coefficients` | 外流气动系数 | `fluent_aero_tutorial.zip` reference CSV | Cd/Cl/Cp、AoA 趋势、压力分布趋势、reference-data ingestion | `static_ready` |
| C05 | `vof_free_surface_transient` | VOF/free-surface 瞬态 | `vof.zip`、legacy `ch10/dambreak` 与 tank flush | alpha 有界性、界面位置、质量守恒、时间步/Courant | `static_ready` |
| C06 | `sliding_rotating_mesh` | 旋转/滑移/运动网格 | `sliding_mesh.zip`、`single_rotating.zip` | moving zone、periodic/rotating interface、时序结果 | `static_ready` |
| C07 | `heat_transfer_energy_balance` | 换热/CHT/能量平衡 | `2d_heat_exchanger_optimizer.zip`、`effusion_cooling.zip`、battery thermal cases | 温度范围、热流、能量平衡、材料/边界一致性 | `static_ready` |
| C08 | `workbench_parameter_integration` | Workbench/参数化工作流 | `workbench_parameter.zip`、`workbench_elbow.zip` | Workbench project import、Design Point、参数和结果回传 | `static_ready` |

## 静态契约

静态契约位于 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml`。它把 C01-C08 作为 Fluent 首批 seed suite 登记，但不声明每个 seed 都已完成 runtime 或 benchmark validation。

- 每个 seed 必须说明 problem definition、governing model、BC/IC、mesh/discretization、solver setup、input parameters、output quantities、benchmark source、validation criteria、perturbation axes 和 risks。
- 每个 seed 默认保持 `benchmark_candidate`，不能把 tutorial replay 或本地 dry-run 自动升级为数值验证。
- 每个 seed 必须区分 `self_generated`、`official_replay`、`comparison` 三条学习路径。
- runtime profile 只记录可配置边界；真实 executable path 必须通过本地环境变量或被忽略的 machine profile 注入。

## C01 Runtime Smoke

C01 已通过 `configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml`、`schemas/fluent_C01_steady_internal_flow_runtime.schema.json` 和 `src/science_capability_registry/fluent/steady_internal_flow_runtime/` 完成一次 Fluent 2025 R1/v251 headless batch smoke。

- 读取 legacy `ch07/elbow` case/data。
- 使用 `2ddp -g -t1` 执行 bounded iteration。
- 对旧 case 的 report-client 路径提示执行显式响应。
- 解析 residual 与 mass-flow report；质量流量平衡误差为 `7.48734375254824e-06`。
- 写入 runtime evidence 到 `_results/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke/`。

该证据只证明 C01 runtime envelope 与 transcript parser 可用；不声明 pressure-drop validation、verification-manual benchmark validation 或 mesh/refinement benchmark。

## C02 Reference Contract

C02 选择 `VMFL005: Poiseuille Flow in a Pipe` 作为第一条 verification reference gate。当前配置复核 Hagen-Poiseuille 压降 `10.24 Pa`，记录手册 Fluent 结果 `10.22 Pa`，并明确当前 source library 未发现官方 `poiseuille-flow.cas` runnable payload。

C02 runtime mesh smoke 使用 `configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke.yaml` 生成 VMFL005 2D axisymmetric half-domain mesh，并通过 Fluent 2025 R1/v251 `2ddp -g -t1` 执行 `mesh/check`。已观测 1280 cells、0 errors。该证据只关闭 mesh-readability blocker，不声明 pressure-drop solve，也不把 C02 升级为 benchmark validated。下一步需要完成 axisymmetric setup、fully developed inlet profile、inlet/outlet pressure sampling 与 mesh trend。

## C04 Reference CSV Parser

C04 已形成 parser/static-readiness 层：`configs/fluent/external_aero_force_coefficients/fluent_aero_reference_csv_static.yaml`、`schemas/fluent_C04_external_aero_force_coefficients.schema.json` 和 `src/science_capability_registry/fluent/external_aero_force_coefficients/`。

本地 source-package run 读取 `fluent_aero_tutorial.zip`，分类 9 个 archive entries，解析 3 个 reference CSV，并验证 ONERA lift curve trend 与两张 Cp section tables。该证据只关闭 reference-data intake，不声明 Fluent solver replay、Cd/Cl force-report extraction、Cp field comparison 或 mesh-independent aero benchmark validation。

## C05 VOF Mesh/Setup Manifest

C05 已形成 mesh/setup source-readiness 层：`configs/fluent/vof_free_surface_transient/vof_inkjet_mesh_setup_static.yaml`、`schemas/fluent_C05_vof_free_surface_transient.schema.json` 和 `src/science_capability_registry/fluent/vof_free_surface_transient/`。

本地 source-package run 读取 `vof.zip`，分类 1 个 archive entry，并确认官方来源是 mesh-only。该证据明确阻止把该包误宣称为 transient VOF solver replay、alpha boundedness、phase conservation 或 interface-motion validation。

## C06 Sliding/Rotating Mesh Setup Manifest

C06 已形成 multi-source mesh/setup 层：`configs/fluent/sliding_rotating_mesh/sliding_rotating_mesh_setup_static.yaml`、`schemas/fluent_C06_sliding_rotating_mesh.schema.json` 和 `src/science_capability_registry/fluent/sliding_rotating_mesh/`。

本地 source-package run 读取官方 `sliding_mesh.zip` 与 legacy `single_rotating.zip`，分类 3 个 mesh entries，并确认两类来源都是 mesh-only。该证据只关闭 source setup readiness，不声明 moving-zone settings、sliding-interface pairing、time history、periodicity 或 solver replay。

## C07 Heat-Transfer Source Manifest

C07 已形成 case/data source-readiness 层：`configs/fluent/heat_transfer_energy_balance/heat_exchanger_case_data_static.yaml`、`schemas/fluent_C07_heat_transfer_energy_balance.schema.json` 和 `src/science_capability_registry/fluent/heat_transfer_energy_balance/`。

本地 source-package run 读取 `2d_heat_exchanger_optimizer.zip`，分类 2 个 archive entries，并确认 1 组匹配的 `.cas.h5` / `.dat.h5`。该证据只关闭 replay input readiness，不声明 temperature extrema、heat-rate balance、CHT interface continuity 或 battery thermal validation。

## C08 Workbench WBPZ Preflight

C08 已形成 Workbench static-preflight 层：`configs/fluent/workbench_parameter_integration/workbench_parameter_wbpz_static.yaml`、`schemas/fluent_C08_workbench_parameter_integration.schema.json` 和 `src/science_capability_registry/fluent/workbench_parameter_integration/`。

本地 source-package run 读取 `workbench_parameter.zip`，打开 nested WBPZ，分类 13 个 Workbench entries，解析 Workbench 2020 R2 metadata，提取当前 P1/P2/P3 input parameters，并记录 DesignPointLog history。该证据只关闭 WBPZ introspection，不声明 RunWB2 execution、project migration、design-point update、result extraction 或 standalone Fluent batch equivalence。

## Failure Ledger

Fluent failure and recovery evidence 已结构化到 `reports/fluent_failure_ledger.yaml`，由 `schemas/fluent_failure_ledger.schema.json` 与 `tests/test_fluent_failure_ledger.py` 保护。

ledger 覆盖 C01 runtime prompt fixes、C02 pressure-solve gaps、C03 mesh-convergence gap、C04 parser-only boundary、C05/C06 mesh-only source boundary、C07 source-readiness-only boundary，以及 C08 WBPZ/RunWB2 separation。未来 Fluent 工作在扩大声明前必须先把失败、阻塞和修复证据补入该 ledger。

## Official Replay Manifest

`configs/fluent/official_replay_manifest/c01_c08_sources.yaml` 统一登记 C01-C08 的官方、legacy、Workbench 与 reference source bindings。当前 manifest 只做 source classification，不解压大文件、不执行 Fluent，也不把 source existence 等同于 solver replay。

该 manifest 明确把 C05/C06 标记为 mesh-only setup seed，把 C08 标记为 Workbench project seed，防止把 mesh 或 `.wbpz` 错当成 standalone Fluent batch 输入。

## 自生成 vs 官方 Replay 学习闭环

每个 seed 后续应形成两条路径：

1. `self_generated`：由 config 生成 Fluent journal 与 case setup，运行并抽取 canonical metrics。
2. `official_replay`：解压官方 zip，识别关键输入文件，运行 Fluent 或 Workbench replay，并抽取同一组 canonical metrics。

比较结果必须分类为 geometry、mesh、model、boundary、unit、initialization、runtime-profile 或 reference mismatch，而不是简单记成“数值不通”。

## 当前禁止声明

- 不声明任一 Fluent seed 已完成 benchmark validation 或 full solver validation，除非对应 evidence 已进入 catalog、report 与 failure ledger。
- 不把 tutorial case 等同于 verification benchmark。
- 不把 Workbench package 等同于 headless 自动化；需要单独的 runtime profile。
- 不提交大型解压数据或 runtime evidence；runtime evidence 只放在 `_results/fluent/`，稳定总结进入 `reports/`。
