# Cantera C01 扰动案例验收报告

## 目的

本报告记录 `C01_constant_pressure_ignition` 在三个参数扰动下的自动验收结果和物理趋势。扰动案例用于验证该 capability 不是固定 demo，而是可参数化、可复现、可解释的 0D 定压点火能力。

## Baseline

- Config: `configs/cantera/c01_constant_pressure_ignition/baseline.yaml`
- Composition: `H2:2,O2:1,N2:4`
- Initial temperature: `1001.0` K
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Ignition delay s | 0.00031501152 |
| Final temperature K | 2665.65 |
| Temperature rise K | 1664.65 |
| Time point count | 160 |

## Case 1: 初始温度升高

- Config: `configs/cantera/c01_constant_pressure_ignition/perturbation_temperature_high.yaml`
- Change: `initial_temperature_k` 从 `1001.0` K 提高到 `1100.0` K
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Ignition delay s | 0.000092112814 |
| Final temperature K | 2703.91 |
| Temperature rise K | 1603.91 |
| Time point count | 160 |

趋势解释：初始温度升高后，氢氧链分支反应更早进入快速放热阶段，点火延迟从约 `0.315 ms` 缩短到约 `0.092 ms`。终态温度略高，符合升温增强反应速率并提前热释放的预期。

## Case 2: 氢气偏稀

- Config: `configs/cantera/c01_constant_pressure_ignition/perturbation_lean_mixture.yaml`
- Change: `composition` 从 `H2:2,O2:1,N2:4` 改为 `H2:1.5,O2:1,N2:4`
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Ignition delay s | 0.00030576171 |
| Final temperature K | 2507.26 |
| Temperature rise K | 1506.26 |
| Time point count | 155 |

趋势解释：氢气偏稀后，终态温度和温升下降，说明可释放化学能减少。点火延迟略短于 baseline，这不是简单“越稀越慢”的单调关系；在该 `h2o2.yaml`、`1001 K`、定压窗口下，氢氧自由基链反应对配比变化具有非线性响应，因此验收时应以温度、物种和点火定义共同判断，而不是只用单一经验趋势。

## Case 3: 氮气稀释增强

- Config: `configs/cantera/c01_constant_pressure_ignition/perturbation_dilution_high.yaml`
- Change: `composition` 从 `H2:2,O2:1,N2:4` 改为 `H2:2,O2:1,N2:6`
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Ignition delay s | 0.00039733796 |
| Final temperature K | 2404.05 |
| Temperature rise K | 1403.05 |
| Time point count | 144 |

趋势解释：氮气稀释增强后，体系热容增加且反应物浓度降低，点火延迟从约 `0.315 ms` 增加到约 `0.397 ms`，终态温度和温升明显下降。这是该 0D 定压点火能力最稳定的稀释方向性验收案例。

## 自动验收结论

- 三个扰动 case 均通过 schema 校验。
- 三个扰动 case 的实际 Cantera 求解均通过自动验收。
- 所有运行均输出 CSV、图、日志、`metrics.json` 和 `validation_report.md`。
- `_results/` 中的运行产物不进入 Git；本报告只沉淀可审计的关键 metrics 和物理趋势。

## 后续

后续如果要把 C01 用作 C05 reaction path analysis 或 C06 mechanism reduction 的上游状态生成器，应把目标状态点、元素选择、误差指标和参考工况集合写成新的 config，而不是直接复用单个 baseline 结果。
