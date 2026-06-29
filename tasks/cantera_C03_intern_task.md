# 将 Cantera 对向扩散火焰官方样例封装为可调用科学能力

## 任务目标

将 Cantera 官方对向扩散火焰 example 封装为个人 workflow 或 MatOS 可调用的 `combustion.cantera.counterflow_diffusion_flame` capability。交付物必须能被负责人自动验收，并能作为后续 workflow stage 的基础。

## 禁止事项

- 不允许只复制官方代码。
- 不允许把网页整理成教程。
- 不允许把输入参数硬编码在脚本里作为唯一运行方式。
- 不允许只证明程序能跑；必须证明求解器收敛、物理趋势合理、输出可被个人 workflow 或 MatOS 集成。

## 必须抽象的输入参数 schema

输入 schema 至少包含：

- `mechanism`：默认 `gri30.yaml`。
- `pressure_pa`：默认 `101325.0`。
- `width_m`：燃料和氧化剂入口间距，默认 `0.02`。
- `fuel_inlet`：温度、质量通量、组成。
- `oxidizer_inlet`：温度、质量通量、组成。
- `radiation_mode`：必须支持 `no_radiation` 和 `radiation`。
- `boundary_emissivities`：辐射边界发射率。
- `refine_criteria`：网格细化参数，包括 `ratio`、`slope`、`curve`、`prune`。
- `outputs`：输出目录、是否保存 CSV、图、日志、报告。

## 功能要求

- 必须支持无辐射和有辐射两种模式。
- 必须输出温度、速度、主要组分、峰值温度、火焰位置。
- 必须保存 CSV、图、日志。
- 必须提供自动验收脚本。
- 必须返回机器可读 summary，例如 `metrics.json`。
- 必须保留 Cantera 求解统计或日志，便于负责人判断收敛过程。

## 输出要求

每次运行至少生成：

- `diffusion_flame_no_radiation.csv`
- `diffusion_flame_radiation.csv`
- `diffusion_flame_temperature.png`
- `diffusion_flame_run.log`
- `metrics.json`
- `validation_report.md`

`metrics.json` 至少包含：

- `no_radiation.peak_temperature_k`
- `no_radiation.flame_position_m`
- `radiation.peak_temperature_k`
- `radiation.flame_position_m`
- `radiation_temperature_drop_k`
- `grid_point_count`
- `converged`

## 自动验收要求

自动验收脚本至少检查：

- 默认 benchmark 在无辐射和有辐射模式下都能完成求解。
- 必需输出文件全部存在且非空。
- 默认无辐射峰值温度在 `1900 K` 到 `2050 K` 之间。
- 默认有辐射峰值温度不高于无辐射峰值温度。
- 默认火焰位置在 `0.0055 m` 到 `0.0070 m` 之间。
- CSV 中温度、速度和主要组分列存在，数值有限。
- 主要组分摩尔分数在数值容差内保持物理有界。

## 参数扰动案例

必须至少给出 3 个参数扰动案例，并解释结果趋势是否物理合理：

- 提高燃料入口质量通量：观察火焰位置是否向氧化剂侧移动，峰值温度和火焰结构是否保持合理。
- 提高氧化剂入口质量通量：观察火焰位置是否向燃料侧移动，速度场和温度峰位置是否符合对向流直觉。
- 改变入口间距 `width_m`：观察温度剖面、网格点数和火焰位置是否随计算域变化而稳定。
- 可选：改变边界发射率或开启辐射，观察峰值温度是否降低。

## 负责人验收口径

负责人不需要亲自学习 Cantera 操作。负责人只根据以下材料验收：

- 资产卡是否完整表达问题类型、物理模型、输入、输出、依赖软件、benchmark、验收标准和集成方式。
- 默认 benchmark 是否通过自动验收。
- 参数扰动趋势解释是否符合燃烧和对向流扩散火焰的物理直觉。
- 输出 artifact 是否能被后续 workflow 读取和比较。

## 交付清单

- Python package 代码。
- 输入 schema。
- 默认 benchmark 配置。
- 3 个以上参数扰动配置。
- 自动验收脚本。
- 运行输出样例。
- 验收报告。
