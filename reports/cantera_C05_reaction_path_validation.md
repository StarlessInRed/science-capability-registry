# Cantera C05 反应路径分析验收报告

## Case

- Capability: `combustion.cantera.reaction_path_analysis`
- Source: Cantera official Python example, `Viewing a reaction path diagram`
- Source URL: `https://cantera.org/stable/examples/python/kinetics/reaction_path.html`
- Mechanism: `gri30.yaml`
- Reactor model: `IdealGasReactor`
- Initial temperature: `1300.0` K
- Pressure: `101325.0` Pa
- Composition: `CH4:0.4,O2:1,N2:3.76`
- Target temperature: `1900.0` K
- Element: `N`
- Label threshold: `0.01`

## Validation Result

- Result: `passed`
- Local Cantera version: `3.2.0`
- Run output directory: `_results/cantera/c05_reaction_path_analysis/baseline`
- Graphviz `dot`: 当前本机未安装，因此官方 graph PNG 未作为默认必需产物；DOT、raw data、CSV 和 flux plot 已通过验收。

## Benchmark Metrics

| Metric | Value |
| --- | ---: |
| Final temperature K | 1900.71 |
| Final time s | 0.00990516 |
| Reactor steps | 1009 |
| Node count | 18 |
| Nonzero edge count | 54 |
| Significant edge count | 27 |
| Maximum absolute net flux | 0.000513737 |

## Scientific Interpretation

该 case 验证的是在一个明确的甲烷氧化动力学状态点上，对指定元素生成 reaction path diagram 的能力。它不是简单保存图片，而是把状态点生成、路径数据解析、边通量表、DOT 图描述和自动验收串成一个可复现 workflow。

baseline 的 N 路径包含 `N2`、`NO`、`NNH`、`HCN`、`NH`、`NCO` 等 expected nodes，说明解析得到的是氮元素相关反应网络，而不是把 `get_data()` 的标题行误当节点。显著边数量和最大净通量均超过配置阈值，能够作为后续机理分析和机理简化的路径证据。

## Generated Artifacts

- `reaction_path.dot`
- `reaction_path_data.txt`
- `reaction_path_edges.csv`
- `reaction_path_top_fluxes.png`
- `reaction_path_run.log`
- `metrics.json`
- `validation_report.md`

## Validation Gate

- schema gate: `passed`
- reactor target state: `passed`
- get_data parser: `passed`
- expected nodes anchor: `passed`
- finite edge fluxes: `passed`
- artifact completeness: `passed`
- optional Graphviz PNG: `not enabled`

## Risks and Limits

- C05 是 kinetics state analysis，不是点火时间计算；若要接 C01，应消费显式序列化的 C01 状态点，而不是混淆两个 capability 的职责。
- `ReactionPathDiagram` 的图布局依赖 Graphviz；当前本机未安装 `dot`，所以第一版以 DOT 和 machine-readable path data 作为核心产物。
- 节点和边通量对目标温度、机理版本和元素选择敏感，后续科研级回归应为每个 case 增加更窄的 reference tolerance。
