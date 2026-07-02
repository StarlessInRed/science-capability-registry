# Fluent C02 Verification Reference Static Readiness

日期：2026-07-02

## 结论

Fluent C02 已从“verification manual 候选源”推进到可执行的静态 reference contract。首个 reference gate 选择 `VMFL005: Poiseuille Flow in a Pipe`，原因是它有清晰的 Hagen-Poiseuille 压降解析式和手册表格目标，比曲线采样或湍流图表更适合作为第一道科学验证门。

## 产物

- config: `configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference.yaml`
- schema: `schemas/fluent_C02_verification_reference_validation.schema.json`
- package: `src/science_capability_registry/fluent/verification_reference_validation/`
- tests: `tests/test_fluent_c02_schema.py`、`tests/test_fluent_c02_runner.py`、`tests/test_fluent_c02_validation.py`
- runtime evidence root: `_results/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_static_reference/`

## Reference Mapping

| item | value |
| --- | --- |
| manual case | VMFL005 |
| title | Poiseuille Flow in a Pipe |
| model | steady laminar incompressible pipe flow |
| pipe length | 0.1 m |
| pipe radius | 0.00125 m |
| mean inlet velocity | 2.0 m/s |
| viscosity | 1.0e-5 kg/(m s) |
| target pressure drop | 10.24 Pa |
| manual Fluent pressure drop | 10.22 Pa |

公式 contract 为 `delta_p = 32 * mu * L * U_mean / D^2`，当前配置复算得到 `10.24 Pa`。手册 Fluent 值相对目标误差约 `0.001953125`，低于当前静态阈值 `0.03`。

## 失败预防

- 不使用本机盘符路径；source provenance 使用 `AgentKnowledge/case_library/fluent/cases/official_tutorials` 逻辑路径。
- 不把 PDF 名称本身当 benchmark；几何、物性、边界条件、公式和目标数值全部进入 config/schema。
- 不声明本地已找到 `poiseuille-flow.cas`；当前 library 未发现该 runnable payload。

## 不声明

- 不声明 Fluent 已运行 VMFL005。
- 不声明 C02 已 `benchmark_validated`。
- 不声明 mesh-independent pressure-drop benchmark；后续至少需要自生成 Fluent case 和三档网格误差趋势。
