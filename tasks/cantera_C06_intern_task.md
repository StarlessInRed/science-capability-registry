# 任务：将 Cantera 机理简化官方样例封装为可调用科学能力

## 目标

把 Cantera 官方 `Mechanism reduction` 样例转化为 `C06_mechanism_reduction` capability。交付物必须能运行详细 n-hexane 机理，按最大相对净反应速率排序反应，生成多个 reduced mechanisms，并用点火温度曲线对比验证简化误差。

官方来源：
`https://cantera.org/stable/examples/python/kinetics/mechanism_reduction.html`

## 不允许的做法

- 不允许只复制官方脚本并把 reduced YAML 扔到当前目录。
- 不允许只输出最小反应数列表，不复跑 reduced mechanisms。
- 不允许只检查 `metrics.json` 存在；必须检查 reaction ranking、reduced YAML 和 profile。
- 不允许把 C06 描述成“自动得到最优机理”。它只是一个 ranking-based benchmark。

## 必须抽象的输入 schema

- `mechanism`：默认 `example_data/n-hexane-NUIG-2015.yaml`。
- `initial_temperature_k`、`pressure_pa`、`equivalence_ratio`、`fuel`、`oxidizer`。
- `reactor_model`：固定为 `ideal_gas_constant_pressure_mole`。
- `simulation.end_time_s`、`simulation.max_steps`、`simulation.use_adaptive_preconditioner`。
- `ranking.metric`：固定为 `max_relative_net_rate_of_progress`。
- `ranking.always_include_species`。
- `reduction.reaction_counts`。
- `outputs`：profiles、ranking、reduced mechanisms、comparison plot、log、metrics、validation report。
- `validation`：全机理规模、终态温度、profile 点数、ranking 数量、reduced case 数量和误差阈值。

## 必须输出的结果

- 全机理 species/reaction count、温度曲线、点火延迟、终态温度。
- reaction ranking CSV，包含 rank、score、equation。
- 每个 reduced mechanism 的 YAML 文件。
- 每个 reduced mechanism 的温度曲线、点火延迟、终态温度、相对误差。
- 温度曲线对比图。
- `metrics.json` 和 `validation_report.md`。

## 自动验收要求

验收脚本必须检查：

- 全机理运行达到 `end_time_s`，温度、压力和 profile 都是有限数。
- ranking 长度覆盖全机理反应数量，score 有限且降序。
- 每个 reduced YAML 存在且可由 Cantera 重新加载。
- 每个 reduced mechanism 的 reaction count 等于配置值。
- 每个 reduced profile 点数足够，点火延迟和终态温度误差可计算。
- 最大 reduced case，例如 `800` reactions，误差低于配置阈值。
- 所有 CSV、YAML、图、日志、metrics 和 report 存在且非空。

## 参数扰动案例

后续至少补充 3 个扰动案例，并解释趋势是否物理合理：

1. 将 `initial_temperature_k` 从 `975 K` 提高到 `1050 K`，预期点火提前，小机理误差可能下降。
2. 将 `pressure_pa` 从 `5 atm` 提高到 `10 atm`，预期压力敏感和第三体反应重要性上升。
3. 将 `equivalence_ratio` 从 `0.8` 改为 `1.0`，预期热释放和终态温度提高，燃料裂解与 CO/CO2 氧化路径权重变化。

每个扰动案例都必须给出配置文件、核心 metrics、趋势解释和自动验收结果。
