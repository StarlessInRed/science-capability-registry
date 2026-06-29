# science-capability-registry

`science-capability-registry` 是个人与 MatOS 均可复用的科学计算能力资产注册层。它不是 MatOS 主代码仓，也不是某个具体科学计算项目的实现仓；它用于沉淀 Cantera、OpenFOAM、Fluent、COMSOL、Abaqus、Gmsh、ParaView 等科学计算软件的能力卡、benchmark、实习生任务和自动验收标准。

## 仓库目标

本仓库把外部科学计算资料转化为个人与 MatOS 都能组织、复用、验证和扩展的能力资产：

- 将网页收藏转化为科学能力资产，而不是教程摘抄。
- 将软件 example 转化为可复现 benchmark，而不是一次性 demo。
- 将 benchmark 转化为 scientific capability，明确输入、输出、依赖软件和接入方式。
- 将 capability 转化为实习生任务和自动验收标准，让实习生可执行、负责人可验收、个人或 MatOS 可集成。

## 目录说明

- `docs/`：科学资产管理方法、个人/MatOS 复用边界和长期设计文档。
- `software/`：按科学计算软件组织的软件能力定位、能力地图和资产卡。
- `capabilities/`：按科学问题域组织的 capability 视角。
- `tasks/`：实习生任务书和负责人验收要求。
- `schemas/`：能力卡、任务、报告等结构化资产的 schema。
- `prompts/`：把网页、example、论文或软件文档转成资产卡的提示词。
- `reports/`：能力验收报告模板和验收记录。

## 当前起点

首个种子资产是 Cantera `C03_counterflow_diffusion_flame`，来源于 Cantera 官方一维对向扩散火焰示例。该资产用于验证从官方 example 到可调用、可验收、可集成燃烧 capability 的资产化流程。
