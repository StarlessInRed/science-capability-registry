# 将 Cantera 扩散火焰熄灭应变率官方样例封装为可调用科学能力

## 任务目标

将 Cantera 官方 `Diffusion flame extinction strain rate` example 封装为 `combustion.cantera.extinction_strain_rate` capability。交付物必须证明该能力不是单次 demo，而是能自动搜索对向扩散火焰熄灭点，并输出可验收的应变率指标。

## 禁止事项

- 不允许只复制官方代码。
- 不允许把网页整理成教程。
- 不允许只报告“程序能跑”。
- 不允许把 continuation 参数、停止条件和输出路径硬编码成唯一运行方式。

## 必须抽象的输入参数 schema

- `mechanism`：默认 `h2o2.yaml`。
- `pressure_pa`：默认 `100000.0`。
- `width_m`：默认 `0.018`。
- `fuel_inlet`：温度、质量通量、组成。
- `oxidizer_inlet`：温度、质量通量、组成。
- `refine_criteria`：`ratio`、`slope`、`curve`、`prune`。
- `scaling_exponents`：网格、速度、spread rate、径向压力梯度、质量通量随应变率变化的缩放指数。
- `extinction_search`：初始 `delta_alpha`、细化因子、最小 `delta_alpha`、最小温度变化、最大迭代次数。
- `outputs`：输出目录、是否保存 solver snapshots、CSV、图、日志、metrics 和 validation report。

## 功能要求

- 必须先求解低应变率初始火焰。
- 必须按官方 scaling rules 增加应变率。
- 必须在火焰熄灭后回退到最后一个仍燃烧解，并细化 `delta_alpha`。
- 必须输出最后一个仍燃烧解的 peak temperature、mean/max strain rate、fuel/oxidizer potential-flow strain rate、stoichiometric strain rate。
- 必须保存温度-最大应变率曲线、迭代历史 CSV、日志、`metrics.json` 和 `validation_report.md`。
- 必须提供自动验收脚本。

## 自动验收要求

- 初始火焰必须收敛。
- 必须至少出现一次仍燃烧解和一次熄灭解。
- 最终 extinction peak temperature 必须为有限值，且高于入口温度上限。
- 最大应变率、平均应变率、stoichiometric strain rate 必须为有限正值。
- `peak_temperature_history_k` 与 `max_strain_rate_history_1_s` 长度必须和 alpha history 对齐。
- 必须生成 CSV、图、日志、metrics 和 validation report。

## 负责人验收口径

负责人不需要亲自学习 Cantera 操作。验收时只看：

- 资产卡是否清楚说明问题类型、物理模型、输入、输出、benchmark 和接入方式。
- 配置是否能表达官方 benchmark 和搜索停止条件。
- 自动验收是否证明求解器收敛、熄灭点搜索有效、应变率指标完整。
- 结果趋势是否符合“应变率提高导致火焰接近熄灭”的物理预期。

