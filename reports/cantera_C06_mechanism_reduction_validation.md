# Cantera C06 机理简化验收报告

## Case

- Capability: `combustion.cantera.mechanism_reduction`
- Source: Cantera official Python example, `Mechanism reduction`
- Source URL: `https://cantera.org/stable/examples/python/kinetics/mechanism_reduction.html`
- Mechanism: `example_data/n-hexane-NUIG-2015.yaml`
- Reactor model: `IdealGasConstPressureMoleReactor`
- Initial temperature: `975.0` K
- Pressure: `506625.0` Pa
- Equivalence ratio: `0.8`
- Fuel: `NC6H14:1.0`
- Oxidizer: `O2:1.0, N2:3.76`
- End time: `0.04` s
- Reaction counts: `100, 200, 300, 400, 600, 800`

## Validation Result

- Result: `passed`
- Local Cantera version: `3.2.0`
- Run output directory: `_results/cantera/c06_mechanism_reduction/baseline`

## Full Mechanism Metrics

| Metric | Value |
| --- | ---: |
| Species count | 1268 |
| Reaction count | 5336 |
| Ignition delay ms | 14.6679 |
| Final temperature K | 2508.04 |
| Profile points | 1280 |

## Reduced Mechanism Metrics

| Reactions | Species | Ignition delay ms | Tau relative error | Final T K | Final T error K |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 64 | 18.487 | 0.260376 | 1712.68 | 795.359 |
| 200 | 108 | 22.8994 | 0.561197 | 2383.66 | 124.378 |
| 300 | 143 | 16.7233 | 0.140128 | 2422.65 | 85.3822 |
| 400 | 171 | 16.8089 | 0.14597 | 2500.27 | 7.76854 |
| 600 | 223 | 15.6334 | 0.0658295 | 2501.86 | 6.17181 |
| 800 | 274 | 15.2307 | 0.0383737 | 2505.05 | 2.98818 |

## Scientific Interpretation

该 case 验证的是基于反应重要性排序的候选机理简化能力。全机理先运行 n-hexane/air 定压点火，记录每个反应在所有时间步上的最大相对净反应速率；随后按排序截取 top `N` reactions，收集相关 species 和强制保留的入口 species，构造 reduced mechanism 并复跑同一 ignition problem。

结果显示，小机理并不保证单调更好：`200` reactions 的点火延迟误差比 `100` reactions 更大。但随着 reaction count 提升到 `600/800`，点火延迟和终态温度都显著接近全机理。`800` reactions 的点火延迟相对误差约 `3.84%`，终态温度误差约 `3 K`，满足当前 capability 级验收阈值。

## Generated Artifacts

- `baseline_profile.csv`
- `reduced_<N>_profile.csv`
- `reaction_ranking.csv`
- `reduction_summary.csv`
- `reduced_mechanisms/reduced_<N>_reaction.yaml`
- `mechanism_reduction_temperature_profiles.png`
- `mechanism_reduction_run.log`
- `metrics.json`
- `validation_report.md`

## Validation Gate

- schema gate: `passed`
- full mechanism ignition run: `passed`
- reaction ranking sorted and finite: `passed`
- reduced mechanism generation: `passed`
- reduced profile integrity: `passed`
- largest reduced mechanism error: `passed`
- artifact completeness: `passed`

## Risks and Limits

- C06 的 ranking metric 是官方示例中的简化指标，不代表机理简化的唯一或最优方法。
- reduced mechanisms 只在当前 n-hexane/air 点火条件下通过验证；进入科研或工程使用前，应增加压力、温度、当量比和目标物种误差矩阵。
- 完整官方矩阵约 12 秒，本仓库将其作为 capability validation，而不是每次轻量单测都执行的 regression。
