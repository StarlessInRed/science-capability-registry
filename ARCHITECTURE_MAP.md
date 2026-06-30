# science-capability-registry 架构边界图

## 仓库角色

`science-capability-registry` 是 Scientific AI Operating System 的科学本体仓库。

它定义科学能力是什么，包括物理模型、数值方法、solver 语义、surrogate model 定义、benchmark 与验证准则。它不负责源数据摄取、认知工具工作流或运行时执行。

## 负责范围

- physics models：物理对象、控制方程、边界条件、材料模型和问题定义。
- numerical methods：FEM、CFD、MD、ODE/PDE、phase-field 等数值方法描述。
- solver systems：Cantera、OpenFOAM、Abaqus、VASP、Gmsh 等科学软件能力定义。
- surrogate models：RomAI 等 surrogate/ROM 能力的科学侧定义，不包含运行时执行逻辑。
- benchmarks：可复现实验、输入输出约束、验证指标和结果报告。

## 当前资产形态

- `software/`：按科学软件组织的能力索引与说明。
- `capabilities/`：能力卡、接口、限制、验证与示例。
- `configs/`：科学能力相关配置样例。
- `schemas/`：能力输入输出和验证 schema。
- `reports/`：运行或验证报告。
- `tasks/`：能力建设任务记录。
- `prompts/`：能力抽取与整理提示词。

## 已知能力域

- Cantera：反应动力学、热力学、火焰、反应器、输运、机理验证等能力域。
- OpenFOAM：不可压缩流、可压缩流、多相流、传热、动网格、湍流、CHT 等能力域。
- Gmsh：几何与网格生成能力域。
- Abaqus、Fluent、COMSOL、VASP 等：可作为科学能力域扩展，不在本文件中假定其完整状态。

## 不负责范围

- 不保存 Bilibili、YouTube、Zotero、Codex、GitHub mining、PDF parsing 等工作流定义。
- 不接收 raw source 作为入口；raw source 必须先经过 `science-intelligence-gateway`。
- 不决定 registry routing；routing authority 只属于 `science-intelligence-gateway`。
- 不执行 solver 或 RomAI runtime；执行属于 `Sci_AI_OS` 和执行后端。

## 边界规则

- 本仓库回答 “WHAT THE PHYSICS IS”。
- workflow adapter 不是 science capability。
- benchmark 是科学验证资产，不是工作流流水线。
- surrogate 的科学定义可在本仓库，surrogate 的训练/推理执行不在本仓库。
