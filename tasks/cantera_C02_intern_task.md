# 任务：将 Cantera 自由传播预混火焰官方样例封装为可调用科学能力

## 目标

把 Cantera 官方 `Laminar flame speed calculation` 样例转化为 `C02_freely_propagating_premixed_flame` capability。交付物必须能被负责人直接运行、验收，并作为个人或 MatOS 工作流中的燃烧能力节点。

官方来源：

`https://cantera.org/stable/examples/python/onedim/adiabatic_flame.html`

## 不允许的做法

- 不允许只复制官方代码后改文件名。
- 不允许把燃料、压力、宽度、网格加密策略、transport model、Soret diffusion 写死在脚本里。
- 不允许只输出一张图或一个 flame speed 数字。
- 不允许用“能跑通 demo”代替科学验收。

## 必须抽象的输入 schema

- `mechanism`：例如 `h2o2.yaml`。
- `pressure_pa`：压力。
- `unburned_temperature_k`：未燃气温度。
- `reactants`：预混气组成，例如 `H2:1.1, O2:1, AR:5`。
- `width_m`：一维计算域宽度。
- `refine_criteria`：至少包括 `ratio`、`slope`、`curve`。
- `transport_modes`：至少支持 mixture-averaged、mixture-averaged + Soret、multicomponent、multicomponent + Soret。
- `outputs`：控制 CSV、图、日志、metrics、validation report、solution snapshot 的保存。
- `validation`：定义 flame speed、峰值温度、温升、热释放率、网格数和组分边界的验收阈值。

## 必须输出的结果

- 每个 transport mode 的 flame speed。
- 网格坐标、速度、温度、密度、热释放率。
- 主要组分 `O2`、`H2`、`H2O` 的摩尔分数剖面。
- 可选次要组分 `OH`、`H`、`O` 的摩尔分数剖面。
- 峰值温度、火焰位置、最大热释放率、网格点数。
- CSV、图、日志、`metrics.json` 和 `validation_report.md`。

## 自动验收要求

验收脚本必须检查：

- 所有配置的 transport mode 均收敛并出现在 metrics 中。
- flame speed 为正，且在配置的参考范围内。
- 峰值温度、燃尽侧温升、最大热释放率符合物理预期。
- 组分摩尔分数有限，且不明显超出 `[0, 1]`。
- 网格点数达到最低要求。
- CSV、图、日志、metrics、报告等产物存在且非空。

## 参数扰动案例

实习生至少补充 3 个扰动案例，并解释趋势是否物理合理：

1. 降低或升高未燃气温度，观察 flame speed 与峰值温度变化。
2. 改变氢气/氧气当量附近配比，观察 flame speed 对混合气反应性的响应。
3. 改变 transport mode 或启用/关闭 Soret diffusion，比较火焰速度和热释放峰位置。

每个扰动案例都必须给出：

- 配置文件；
- 运行命令；
- 核心 metrics；
- 趋势解释；
- 是否通过自动验收。

## 负责人验收口径

负责人不需要亲自学习 Cantera 操作界面或逐行理解官方脚本，但必须能判断：

- 这个能力解决的是一维自由传播预混火焰和层流火焰速度问题；
- 物理模型、边界条件、网格策略、transport model 和 Soret diffusion 已被显式配置；
- 输出不是 demo 截图，而是可复现的 profile、metrics 和报告；
- 结果趋势符合燃烧物理常识；
- 该 capability 可以作为后续燃烧工作流的可调用节点。
