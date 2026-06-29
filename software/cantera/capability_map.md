# Cantera 能力地图

| 编号 | 能力名称 | 问题类型 | 资产化目标 |
| --- | --- | --- | --- |
| C01 | constant-pressure ignition | 0D 定压点火 | 输入机理、初始温度、压力、组成和积分步长，输出点火延迟、温度/压力/内能/焓曲线和关键组分曲线；当前已有 C01 资产卡、baseline/perturbation config、package 和自动验收报告。 |
| C02 | freely propagating premixed flame | 一维自由传播预混火焰 | 输入预混气、压力、温度、计算域宽度、网格加密策略和 transport/Soret 模式，输出火焰速度、温度/组分/热释放剖面；当前已有 C02 资产卡、baseline config、package 和自动验收报告。 |
| C03 | counterflow diffusion flame | 一维对向扩散火焰 | 输入燃料/氧化剂入口、质量通量、间距和辐射模式，输出火焰结构、峰值温度和火焰位置。 |
| C04 | extinction strain rate | 扩散火焰熄灭极限 | 扫描拉伸率或质量通量，输出熄灭边界、收敛状态、临界趋势和应变率指标；当前已有 C04 资产卡与 baseline config。 |
| C05 | reaction path analysis | 反应路径分析 | 输入机理、反应器状态、目标温度和目标元素，输出 reaction path DOT、raw data、CSV edge table、top flux plot、metrics 和自动验收报告；当前已有 C05 资产卡、baseline/perturbation config、package 和 benchmark 报告。 |
| C06 | mechanism reduction | 机理简化 | 输入详细机理、工况集合和误差阈值，输出简化机理和误差评估。 |
