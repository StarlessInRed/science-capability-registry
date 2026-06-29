# Cantera C01 定压点火验收报告

## Case

- Capability: `combustion.cantera.constant_pressure_ignition`
- Source: Cantera official Python example, `Constant-pressure, adiabatic kinetics simulation`
- Source URL: `https://cantera.org/stable/examples/python/reactors/reactor1.html`
- Mechanism: `h2o2.yaml`
- Reactor model: `IdealGasConstPressureReactor`
- Initial temperature: `1001.0` K
- Pressure: `101325.0` Pa
- Composition: `H2:2,O2:1,N2:4`
- Time horizon: `1.0e-3` s
- Temperature advance limit: `20.0` K

## Validation Result

- Result: `passed`
- Local Cantera version: `3.2.0`
- Run output directory: `_results/cantera/c01_constant_pressure_ignition/baseline`

## Benchmark Metrics

| Metric | Value |
| --- | ---: |
| Ignition delay s | 0.00031501152 |
| Ignition delay method | `max_temperature_derivative` |
| Final temperature K | 2665.65 |
| Temperature rise K | 1664.65 |
| Maximum saved temperature step K | 20.0 |
| Time point count | 160 |

## Scientific Interpretation

该 case 验证的是 0D 均相、绝热、定压氢氧有限速率点火能力。输入不是任意脚本常量，而是由 schema 约束的机理、初始温度、压力、组成、积分步长、温度 advance limit 和点火延迟定义。

本地结果的终态温度约 `2665.65 K`，与官方样例末端温度量级一致。点火延迟按最大 `dT/dt` 所在时间定义，约为 `0.315 ms`。压力保持在定压容差内，关键组分摩尔分数有界，profile 从 `t=0` 初始状态开始记录，因此能够验证初值、时间单调性和事件位置。

## Generated Artifacts

- `ignition_profile.csv`
- `ignition_temperature_species.png`
- `ignition_run.log`
- `metrics.json`
- `validation_report.md`

## Validation Gate

- schema gate: `passed`
- profile completeness: `passed`
- integration end time: `passed`
- ignition delay range and boundary position: `passed`
- pressure invariance: `passed`
- species bounds: `passed`
- artifact completeness: `passed`

## Risks and Limits

- 该能力是 0D 反应器点火，不包含空间输运、网格、火焰传播速度或 CFD 边界条件。
- 点火延迟定义会影响数值结果；当前默认使用最大 `dT/dt`，`oh_peak` 只能在显式追踪 `OH` 时使用。
- `pressure_high` 在当前 `1 ms` benchmark 窗口内没有形成有效点火，因此没有作为第一阶段通过型扰动 case 登记；后续若要研究压力效应，应单独建立更长时间窗口或压力扫描 benchmark。
