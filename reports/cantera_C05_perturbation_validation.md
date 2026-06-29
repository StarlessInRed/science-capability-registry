# Cantera C05 扰动案例验收报告

## 目的

本报告记录 `C05_reaction_path_analysis` 在三个扰动下的自动验收结果和物理趋势。扰动案例用于证明该 capability 不是 hardcoded 的 N 图，而是可参数化的反应路径分析能力。

## Baseline

- Config: `configs/cantera/c05_reaction_path_analysis/baseline.yaml`
- Element: `N`
- Target temperature: `1900.0` K
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Final temperature K | 1900.71 |
| Final time s | 0.00990516 |
| Step count | 1009 |
| Node count | 18 |
| Nonzero edge count | 54 |
| Significant edge count | 27 |
| Maximum absolute net flux | 0.000513737 |

## Case 1: 切换到碳元素路径

- Config: `configs/cantera/c05_reaction_path_analysis/perturbation_element_carbon.yaml`
- Change: `element` 从 `N` 改为 `C`
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Final temperature K | 1900.71 |
| Final time s | 0.00990516 |
| Step count | 1009 |
| Node count | 34 |
| Nonzero edge count | 141 |
| Significant edge count | 122 |
| Maximum absolute net flux | 27.538 |

趋势解释：碳路径从氮氧化物网络切换到甲烷氧化和烃中间体网络，节点和边显著增加，最大净通量远高于 N 路径。这符合甲烷燃烧中碳元素主反应通量占主导的预期。

## Case 2: 切换到氧元素路径

- Config: `configs/cantera/c05_reaction_path_analysis/perturbation_element_oxygen.yaml`
- Change: `element` 从 `N` 改为 `O`
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Final temperature K | 1900.71 |
| Final time s | 0.00990516 |
| Step count | 1009 |
| Node count | 26 |
| Nonzero edge count | 108 |
| Significant edge count | 87 |
| Maximum absolute net flux | 44.2648 |

趋势解释：氧路径突出氧化剂、自由基和氧化产物之间的元素流动，`O2/O/OH/H2O/CO/CO2` 等 expected nodes 被解析到。其 flux scale 大于 N 路径，符合氧元素直接参与主氧化过程的预期。

## Case 3: 提高目标温度

- Config: `configs/cantera/c05_reaction_path_analysis/perturbation_target_temperature_high.yaml`
- Change: `target_temperature_k` 从 `1900.0` K 提高到 `2000.0` K，元素仍为 `N`
- Result: `passed`

| Metric | Value |
| --- | ---: |
| Final temperature K | 2001.44 |
| Final time s | 0.00990696 |
| Step count | 1043 |
| Node count | 18 |
| Nonzero edge count | 54 |
| Significant edge count | 39 |
| Maximum absolute net flux | 0.0027519 |

趋势解释：提高目标温度后，N 路径的节点族保持一致，但显著边数量从 `27` 增至 `39`，最大净通量从约 `5.14e-4` 增至约 `2.75e-3`。这说明高温状态下更多氮相关反应路径达到显著通量水平。

## 自动验收结论

- 三个扰动 case 均通过 schema 校验。
- 三个扰动 case 的 Cantera 求解均达到目标温度并通过自动验收。
- 每个 case 均输出 DOT、raw data、CSV、flux plot、log、`metrics.json` 和 `validation_report.md`。
- `_results/` 中的运行产物不进入 Git；本报告只沉淀关键 metrics、趋势解释和验收结论。

## 后续

后续若安装 Graphviz，可把 `outputs.save_graph_png` 打开，让 C05 同时生成官方风格 reaction path PNG，并把 PNG header 与图尺寸纳入验收。科研级扩展应加入关键 edge share、目标元素 family 分类和跨机理版本的回归范围。
