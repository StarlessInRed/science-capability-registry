# Cantera C03 基线验收记录

## 验收对象

- 能力：`combustion.cantera.counterflow_diffusion_flame`
- 资产卡：`software/cantera/assets/C03_counterflow_diffusion_flame.yaml`
- 配置：`configs/cantera/c03_counterflow_diffusion_flame/baseline.yaml`
- 软件：Cantera `3.2.0`
- Python：`C:\Users\admin\.conda\envs\romaicpu\python.exe`
- 验收日期：2026-06-29

## Benchmark 定义

该基线对应 Cantera 官方一维对向扩散火焰示例：乙烷燃料入口与空气氧化剂入口相向流动，使用 `gri30.yaml` 机理、混合平均输运和自适应一维网格求解稳态扩散火焰。

关键输入如下：

- 压力：`101325.0 Pa`
- 入口间距：`0.02 m`
- 燃料入口：`C2H6:1`，`300 K`，`0.24 kg/m2/s`
- 氧化剂入口：`O2:0.21, N2:0.78, AR:0.01`，`300 K`，`0.72 kg/m2/s`
- 网格细化：`ratio=4, slope=0.2, curve=0.3, prune=0.04`
- 模式：`no_radiation` 与 `radiation`

## 运行结果

| 指标 | no_radiation | radiation |
| --- | ---: | ---: |
| 收敛状态 | true | true |
| 峰值温度 K | 1981.113759 | 1966.586512 |
| 火焰位置 m | 0.0064375 | 0.0064375 |
| 网格点数 | 96 | 96 |

辐射模式相对无辐射模式的峰值温度降低：

```text
14.52724763975948 K
```

## 自动验收结论

自动验收通过，核心检查包括：

- 无辐射和有辐射两种模式均收敛。
- 无辐射峰值温度位于 `1900 K` 到 `2050 K` 验收范围内。
- 火焰位置位于 `0.0055 m` 到 `0.0070 m` 验收范围内。
- 有辐射峰值温度低于无辐射峰值温度，趋势物理合理。
- 主要组分摩尔分数保持有限并处于数值容差允许范围内。
- CSV、温度图、日志、`metrics.json` 和 `validation_report.md` 均已生成且非空。

## 运行产物

运行态产物保存在 `_results/`，不作为仓库长期正源：

```text
_results/cantera/c03_counterflow_diffusion_flame/baseline/diffusion_flame_no_radiation.csv
_results/cantera/c03_counterflow_diffusion_flame/baseline/diffusion_flame_radiation.csv
_results/cantera/c03_counterflow_diffusion_flame/baseline/diffusion_flame_temperature.png
_results/cantera/c03_counterflow_diffusion_flame/baseline/diffusion_flame_run.log
_results/cantera/c03_counterflow_diffusion_flame/baseline/metrics.json
_results/cantera/c03_counterflow_diffusion_flame/baseline/validation_report.md
```

## 负责人判断

C03 已经从官方 example 进入可运行 benchmark 阶段。当前证据足以证明：

- 输入 schema 能表达官方基线案例。
- runner 能调用 Cantera 完成对向扩散火焰求解。
- 自动验收能检查收敛性、物理趋势、数值范围和输出完整性。

后续工作：

- 根据更多机理、压力和应变率案例决定是否收紧或分层验收阈值。
- 将 baseline 与扰动 case 纳入批量运行入口。
- 在 capability registry 中登记该 benchmark 的稳定版本。
