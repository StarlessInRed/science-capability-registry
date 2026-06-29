# Cantera C04 熄灭应变率验收记录

## 验收对象

- 能力：`combustion.cantera.extinction_strain_rate`
- 资产卡：`software/cantera/assets/C04_extinction_strain_rate.yaml`
- 配置：`configs/cantera/c04_extinction_strain_rate/baseline.yaml`
- 软件：Cantera `3.2.0`
- Python：`C:\Users\admin\.conda\envs\romaicpu\python.exe`
- 验收日期：2026-06-29

## Benchmark 定义

该 benchmark 对应 Cantera 官方 `Diffusion flame extinction strain rate` 示例：在 `1 bar` 条件下求解氢氧对向扩散火焰，通过 Fiala and Sattelmayer scaling rules 逐步提高应变率，直到火焰熄灭，然后回退到最后一个仍燃烧解作为 extinction point。

关键输入如下：

- 机理：`h2o2.yaml`
- 压力：`100000.0 Pa`
- 入口间距：`0.018 m`
- 燃料入口：`H2:1`，`300 K`，`0.5 kg/m2/s`
- 氧化剂入口：`O2:1`，`500 K`，`3.0 kg/m2/s`
- 网格细化：`ratio=3.0, slope=0.1, curve=0.2, prune=0.03`
- continuation 停止条件：`delta_alpha_min=0.001`，`delta_temperature_min_k=1.0`

## 运行结果

| 指标 | 数值 |
| --- | ---: |
| continuation 迭代次数 | 416 |
| 最后燃烧解 alpha | 281.6995683199991 |
| extinction peak temperature K | 1552.445061 |
| mean strain rate 1/s | 157814.421858 |
| max strain rate 1/s | 653702.219234 |
| fuel potential-flow strain rate 1/s | 311749.442605 |
| oxidizer potential-flow strain rate 1/s | 101021.521992 |
| stoichiometric strain rate 1/s | 270655.842645 |

## 自动验收结论

自动验收通过，核心检查包括：

- alpha history、peak temperature history、max strain rate history 和状态序列长度一致。
- 搜索过程中同时包含仍燃烧解和熄灭解。
- 最后燃烧解的 peak temperature 为有限值，并落在 `1200 K` 到 `3000 K` 验收范围内。
- 最大应变率为有限正值，并落在 `1000 1/s` 到 `800000 1/s` 验收范围内。
- mean、max、fuel-side potential-flow、oxidizer-side potential-flow 和 stoichiometric strain rate 均为有限正值。
- 搜索历史中出现峰值温度降到入口温度上限附近的熄灭状态。
- CSV、温度-应变率曲线、日志、HDF snapshots、`metrics.json` 和 `validation_report.md` 均已生成且非空。

## 物理趋势判断

随着应变率增加，峰值温度从初始约 `3053 K` 持续下降，并在 `alpha≈281.7` 附近出现熄灭。最后恢复的燃烧解峰值温度约为 `1552 K`，说明该能力不是单次火焰求解，而是完成了“增加应变率、检测熄灭、回退最后燃烧解、细化搜索”的 benchmark 流程。

最大应变率约为 `6.54e5 1/s`，明显高于初始低应变率火焰，符合“提高拉伸率导致扩散火焰接近熄灭”的物理预期。

## 运行产物

运行态产物保存在 `_results/`，不作为仓库长期正源：

```text
_results/cantera/c04_extinction_strain_rate/baseline/extinction_summary.csv
_results/cantera/c04_extinction_strain_rate/baseline/figure_T_max_a_max.png
_results/cantera/c04_extinction_strain_rate/baseline/diffusion_flame_extinction_run.log
_results/cantera/c04_extinction_strain_rate/baseline/flame_data.h5
_results/cantera/c04_extinction_strain_rate/baseline/metrics.json
_results/cantera/c04_extinction_strain_rate/baseline/validation_report.md
```

## 负责人判断

C04 已经从官方 example 进入可运行 benchmark 阶段。当前证据足以证明：

- 输入 schema 能表达官方熄灭应变率搜索参数。
- runner 能调用 Cantera 完成 continuation、熄灭检测和最后燃烧解恢复。
- 自动验收能检查历史一致性、熄灭状态、应变率指标和输出完整性。

后续工作：

- 将 C03 和 C04 串成 Cantera 对向扩散火焰 capability family。
- 增加压力、入口质量通量和机理扰动案例，形成熄灭边界扫描能力。
- 将 C04 的 `max_iterations` 和 snapshot 保存策略分成 quick / full 两种运行配置。

