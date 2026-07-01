# Scientific Capability Failure Lessons

日期：2026-07-02

## 结论

失败不是附属噪声，而是科学能力资产的一部分。OpenFOAM 和 Gmsh 的首批构筑说明：一个能力卡真正有价值，不只是因为最终 `passed`，还因为它记录了哪些 gate 不该混用、哪些 reference 不同构、哪些 runtime profile 是环境问题、哪些 solver 输出只是 artifact 存在而不是物理验证。

## 失败资产的处理原则

1. 先分类：setup failure、numerical failure、physical failure、evidence failure、reference mismatch、runtime-profile mismatch。
2. 再降阶：把失败从 benchmark gate 降到 diagnostic、smoke、case-freeze 或 promotion gap，而不是直接放宽阈值。
3. 保留 `do_not_claim`：每个失败都要告诉后续 agent 和实习生不能声称什么。
4. 把修复路径写成可恢复队列：失败必须能从报告、ledger、config 或 test 里恢复，不依赖对话记忆。
5. 把环境差异和能力差异分开：v2112/v2412、WSL、本机 license、native functionObject、MATLAB/COMSOL API 都必须单独入账。

## 已沉淀的模式

| 模式 | OpenFOAM/Gmsh 例子 | 对 Fluent/COMSOL 的规则 |
| --- | --- | --- |
| 官方 tutorial 不等于外部 benchmark | OpenFOAM C02/C05 的有限域 reference mismatch | Fluent/COMSOL 先写 reference policy，再绑定数值阈值 |
| artifact 存在不等于物理验证 | Gmsh C06 meshio import 通过，但不代表 FEM solve 通过 | COMSOL mesh import、study run、结果验证必须拆 gate |
| runtime profile 不是 capability 本体 | OpenFOAM v2112/v2412 functionObject 和 sampling 差异 | Fluent license/profile、COMSOL server/MATLAB bridge 必须独立记录 |
| CAD 成功导入不等于 healing 正确 | Gmsh C04 STEP/BREP import 后仍需 entity-map | CAD/geometry chain 必须记录 imported/modified/deleted/new entities |
| proxy 可用于 case-freeze，不可替代 promotion | OpenFOAM C03/C07 proxy postprocess | MATLAB postprocess 可以做 smoke，但 benchmark promotion 要有 native 或独立校验 |

## C01-C06 为什么作为每个科学资产的首批场景

C01-C06 不是固定物理题目，而是一个“首批能力覆盖模板”。它强制每个科学软件先覆盖六类最容易决定资产可用性的能力面：

| 编号 | 首批角色 | 目的 |
| --- | --- | --- |
| C01 | 最小可执行基线 | 证明软件能被配置驱动、能运行、能产出 metrics 和 validation |
| C02 | 解析或强 reference 验证 | 防止只跑 demo，不知道数值是否对 |
| C03 | 网格/离散/收敛或扰动趋势 | 验证能力不是单点偶然通过 |
| C04 | 几何、边界、复杂输入或工程工作流 | 覆盖真实工程里最常见的输入复杂性 |
| C05 | 瞬态、非线性、时序或特征量提取 | 验证 postprocess、时间尺度和稳定性 |
| C06 | 下游集成或多目标 consumability | 验证结果能被另一个 solver、流程或 agent 使用 |

不同软件会把这六类映射到不同场景。Cantera 的 C01-C06 是反应/火焰/机理能力，Gmsh 的 C01-C06 是 geometry/mesh/import 能力，Fluent 的 C01-C06 应偏 CFD setup/solver/postprocess，MATLAB 驱动 COMSOL 的 C01-C06 应偏模型构建/API 驱动/mesh/study/result extraction。

## 给下一批资产的执行约束

- Fluent 首批 C01-C06 不应只是 Fluent tutorial 列表；每个 C 都要有 schema、config、runner 或明确的 license/runtime 边界。
- MATLAB 驱动 COMSOL 必须先把 COMSOL server/MATLAB API 可达性作为 C01 runtime profile，不要直接跳到复杂多物理。
- 每个失败都要进入 report 或 ledger，尤其是 license、GUI/headless、路径映射、单位、边界命名、native postprocess 缺失。
