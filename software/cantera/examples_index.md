# Cantera examples_index

本文件登记已转化或待转化为科学能力资产的 Cantera 官方 example、文档案例和 benchmark 来源。

| ID | 来源 | capability | domain | 资产卡 | benchmark 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | Cantera official Python example: Constant-pressure, adiabatic kinetics simulation | constant-pressure ignition | combustion | `software/cantera/assets/C01_constant_pressure_ignition.yaml` | benchmark validated | 氢气/氧气/N2 定压绝热反应器，已封装为可运行 package，输出温度、压力、内能、焓、点火延迟和 OH/H/H2 等关键组分随时间变化。 |
| C02 | Cantera official Python example: Laminar flame speed calculation | freely propagating premixed flame | combustion | `software/cantera/assets/C02_freely_propagating_premixed_flame.yaml` | benchmark validated | 氢气/氧气/氩气自由传播预混平面火焰，覆盖 mixture-averaged、multicomponent 和 Soret diffusion 对 flame speed 的影响。 |
| C03 | Cantera official Python example: Counterflow diffusion flame | counterflow diffusion flame | combustion | `software/cantera/assets/C03_counterflow_diffusion_flame.yaml` | benchmark candidate | 对向扩散火焰，覆盖无辐射/有辐射两种模式。 |
| C04 | Cantera official Python example: Diffusion flame extinction strain rate | extinction strain rate | combustion | `software/cantera/assets/C04_extinction_strain_rate.yaml` | benchmark candidate | 氢氧对向扩散火焰熄灭搜索，输出最后燃烧解的多种应变率指标。 |
| C05 | Cantera official Python example: Viewing a reaction path diagram | reaction path analysis | combustion | `software/cantera/assets/C05_reaction_path_analysis.yaml` | benchmark validated | 甲烷氧化状态点上的元素 reaction path analysis，输出 DOT、raw data、CSV edge table、flux plot、metrics 和 validation report。 |
| C06 | Cantera official Python example: Mechanism reduction | mechanism reduction | combustion | `software/cantera/assets/C06_mechanism_reduction.yaml` | benchmark validated | n-hexane 详细机理按最大相对净反应速率排序并生成 reduced mechanisms，输出温度曲线、ranking、reduced YAML、误差表和 validation report。 |
