# 任务：将 Cantera 定压点火官方样例封装为可调用科学能力

## 目标

把 Cantera 官方 `Constant-pressure, adiabatic kinetics simulation` 样例转化为 `C01_constant_pressure_ignition` capability。交付物必须能被负责人直接运行、验收，并作为后续 reaction path analysis 与 mechanism reduction 的基础 benchmark。

官方来源：

`https://cantera.org/stable/examples/python/reactors/reactor1.html`

## 不允许的做法

- 不允许只复制官方代码后改文件名。
- 不允许把机理、温度、压力、组成、时间步长和点火延迟定义写死在脚本里。
- 不允许只输出终态温度或一张图。
- 不允许用“能跑通 demo”代替自动验收。

## 必须抽象的输入 schema

- `mechanism`：例如 `h2o2.yaml`。
- `reactor_model`：固定为 `ideal_gas_constant_pressure`。
- `initial_temperature_k`：初始温度。
- `pressure_pa`：定压反应器压力。
- `composition`：初始气体组成。
- `ignition_delay_method`：至少支持 `max_temperature_derivative`，可扩展 `oh_peak`。
- `advance`：`dt_max_s`、`t_end_s`、`temperature_advance_limit_k`、`verbose`。
- `outputs`：CSV、图、日志、metrics、validation report 和跟踪组分。
- `validation`：终态温度、温升、点火延迟、压力误差、时间点数和组分边界。

## 必须输出的结果

- 时间、温度、压力、内能剖面。
- 关键组分摩尔分数，例如 `OH`、`H`、`H2`、`O2`、`H2O`。
- 点火延迟、最大 `dT/dt`、OH 峰值时间。
- 终态温度、温升、压力保持误差。
- CSV、图、日志、`metrics.json` 和 `validation_report.md`。

## 自动验收要求

验收脚本必须检查：

- 反应器积分到配置的终止时间，且时间点数达到最低要求。
- 点火延迟有限、为正，并落入配置范围。
- 终态温度和温升符合参考范围。
- 压力保持在定压容差内。
- 关键组分摩尔分数有限且不明显超出 `[0, 1]`。
- CSV、图、日志、metrics、报告等产物存在且非空。

## 参数扰动案例

至少补充 3 个扰动案例，并解释趋势是否物理合理：

1. 提高初始温度，预期点火延迟缩短。
2. 提高氮气稀释比例，预期点火延迟变长，终态温度和温升下降。
3. 改变氢气/氧气比例，解释温升、终态温度和点火延迟的变化；如果点火延迟不呈简单单调变化，必须从氢氧有限速率动力学角度解释。

每个扰动案例都必须给出配置文件、运行命令、核心 metrics、趋势解释和自动验收结果。
