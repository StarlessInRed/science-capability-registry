# 任务：将 OpenFOAM 顶盖驱动方腔官方 tutorial 封装为可验证科学能力

## 目标

把 OpenFOAM.com 官方 `Lid-driven cavity flow` tutorial 转化为 `C01_lid_driven_cavity_incompressible_laminar` capability。交付物必须让负责人能够判断该能力是否正确表达了不可压缩层流、有限体积离散、PISO 压力-速度耦合、二维空边界和基础 OpenFOAM 运行证据。

官方来源：

`https://www.openfoam.com/documentation/tutorial-guide/2-incompressible-flow/2.1-lid-driven-cavity-flow`

官方 tutorial path：

`$FOAM_TUTORIALS/incompressible/icoFoam/cavity/cavity`

## 不允许的做法

- 不允许只复制 tutorial case 文件夹后声称完成能力封装。
- 不允许把 solver、网格、边界条件、时间步长、残差阈值和后处理目标写死在脚本里。
- 不允许只检查 OpenFOAM 进程退出码；必须解析科学和数值指标。
- 不允许在没有本地 solver metrics、validation summary、报告和测试证据时把状态标成 `benchmark_validated`。
- 不允许把高 Re 或 `pisoFoam` 湍流扩展混入 C01 baseline；那只能作为后续扩展或扰动任务。

## 必须抽象的输入 schema

- `openfoam_distribution`：例如 `openfoam_com`、`openfoam_foundation`。
- `openfoam_version`：版本或 runtime profile 标签。
- `backend`：至少支持 `dry_run_only`，后续可扩展 `wsl`、`native_linux` 或 `docker`。
- `solver`：baseline 为 `icoFoam`。
- `geometry`：方腔边长、二维厚度、坐标方向。
- `mesh`：`blockMesh`、单块 hexahedral 网格、`nx/ny/nz`、`simpleGrading`。
- `material`：运动黏度 `nu`，并能由 `Re = U d / nu` 推导或校验。
- `fields`：`U`、`p` 的 dimensions、internalField 和 boundaryField。
- `boundary_conditions`：`movingWall`、`fixedWalls`、`frontAndBack`。
- `numerics`：`fvSchemes`、`fvSolution`、PISO 参数、线性求解器和容差。
- `time_controls`：`startTime`、`endTime`、`deltaT`、`writeInterval`。
- `outputs`：日志、CSV、图、`metrics.json`、`validation_report.md`、中心线采样。
- `validation`：mesh 拓扑、Courant 数、残差、连续性误差、边界条件保持、压力相对分布、速度回流结构和产物完整性阈值。

## 必须输出的结果

- dry-run manifest：列出将生成的 `0/`、`constant/`、`system/` 字典、OpenFOAM 命令、预期产物和验收目标。
- 生成的 case 文件：`0/U`、`0/p`、`constant/transportProperties`、`system/blockMeshDict`、`system/controlDict`、`system/fvSchemes`、`system/fvSolution`。
- OpenFOAM 执行后输出：`blockMesh` 日志、`icoFoam` 日志、时间目录、`U/p` 场。
- 后处理产物：中心线速度剖面 CSV、压力/速度图、Courant 数与残差摘要、`metrics.json`、`validation_report.md`。

## 自动验收要求

验收脚本必须检查：

- 资产卡通过 `schemas/capability_card.schema.json`，且没有旧的顶层 `status` 字段。
- config 通过 C01 run schema，未知 key 必须 fail fast。
- dry-run manifest 完整列出 case 字典、命令、输出和验证项。
- `blockMesh` 成功，网格为 `20 x 20 x 1` baseline，`frontAndBack` 为 `empty`。
- `icoFoam` 达到 `t=0.5 s`，并写出配置的时间目录。
- 最大 Courant 数不大于 1。
- 残差、连续性误差和场值范围为有限数。
- `movingWall` 速度保持为 `(1 0 0)`，`fixedWalls` 满足 no-slip，二维空边界没有被误建成普通 wall。
- 压力只验证相对分布或压差，不验证绝对偏置。
- 产物文件存在且非空：日志、CSV、图、`metrics.json`、`validation_report.md`。

## 参数扰动案例

至少补充 3 个扰动案例，并解释趋势是否物理合理：

1. 网格分辨率从 `20 x 20 x 1` 提高到 `40 x 40 x 1`，检查中心线速度剖面和回流结构是否趋于稳定。
2. 通过降低 `nu` 或提高顶盖速度提高 Reynolds number，检查回流中心位置、速度梯度和稳定性变化；不要把高 Re 湍流扩展混入 baseline。
3. 缩小或增大 `deltaT`，检查 Courant 数、残差和时间推进稳定性；违反 Courant 约束时必须失败或标记风险。

每个扰动案例都必须给出配置文件、运行命令、核心 metrics、趋势解释和自动验收结果。

## 负责人验收路径

1. 先验收 capability card、examples index 和 intern task 是否完整表达科学能力。
2. 再验收 schema/config 和 dry-run manifest，确认科学选择全部进入配置。
3. 最后在具备 OpenFOAM runtime profile 后运行 baseline 和扰动案例，只有本地 `metrics.json`、validation summary、报告和测试都通过后，才能把 `benchmark_status` 从 `benchmark_candidate` 提升。
