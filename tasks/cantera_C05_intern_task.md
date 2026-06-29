# 任务：将 Cantera 反应路径分析官方样例封装为可调用科学能力

## 目标

把 Cantera 官方 `Viewing a reaction path diagram` 样例转化为 `C05_reaction_path_analysis` capability。交付物必须能从结构化配置生成反应状态点，按目标元素输出 reaction path diagram，并通过自动验收证明图、数据和报告可复现。

官方来源：
`https://cantera.org/stable/examples/python/kinetics/reaction_path.html`

## 不允许的做法

- 不允许只运行官方脚本并保存一张 PNG。
- 不允许把 `gri30.yaml`、`1300 K`、`CH4:0.4,O2:1,N2:3.76`、`element=N` 写死在代码里。
- 不允许只检查文件存在，不解析 `ReactionPathDiagram.get_data()`。
- 不允许在没有 Graphviz `dot` 的环境中把官方 graph PNG 标记为通过。

## 必须抽象的输入 schema

- `mechanism`：例如 `gri30.yaml`。
- `reactor_model`：固定为 `ideal_gas_constant_volume`。
- `initial_temperature_k`、`pressure_pa`、`composition`。
- `target_temperature_k`、`max_time_s`、`max_steps`。
- `element`：反应路径目标元素。
- `diagram.label_threshold` 和 `diagram.title`。
- `outputs`：DOT、Graphviz PNG、raw data、CSV、flux plot、log、metrics、validation report。
- `validation`：终态温度范围、最大时间、最少节点/边/显著边、通量阈值、expected nodes。

## 必须输出的结果

- 终态反应器状态：温度、压力、时间、积分步数。
- reaction path 节点、边、forward/reverse/net flux、top edges。
- `reaction_path.dot`。
- `reaction_path_data.txt`。
- `reaction_path_edges.csv`。
- `reaction_path_top_fluxes.png`。
- `reaction_path_run.log`、`metrics.json`、`validation_report.md`。
- 如果启用 Graphviz，则输出并验收 `reaction_path_graph.png`。

## 自动验收要求

验收脚本必须检查：

- 反应器达到配置的 `target_temperature_k`，且未超过 `max_time_s` 和 `max_steps`。
- `get_data()` 解析时正确区分可选标题行、节点 header 和 edge rows。
- 节点包含配置的 expected nodes，例如 N 路径下的 `N2`、`NO`、`NNH`、`HCN`、`NH`、`NCO`。
- 边通量全部为有限数值，且显著边数量和最大净通量超过阈值。
- DOT、raw data、CSV、flux plot、log、metrics、report 均存在且非空。
- 如果启用 Graphviz PNG，必须检查 PNG header，而不是只检查路径。

## 参数扰动案例

至少补充 3 个扰动案例，并解释趋势是否物理合理：

1. 将 `element` 从 `N` 改为 `C`，预期碳氧化和烃中间体路径更密，flux scale 明显增大。
2. 将 `element` 从 `N` 改为 `O`，预期氧化和自由基交换路径更密，`O2/O/OH/H2O/CO/CO2` 等节点出现。
3. 将 `target_temperature_k` 从 `1900 K` 提高到 `2000 K`，预期 N 路径节点族基本一致，但显著边数量和最大净通量上升。

每个扰动案例都必须给出配置文件、核心 metrics、趋势解释和自动验收结果。
