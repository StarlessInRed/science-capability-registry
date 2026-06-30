# science-capability-registry 系统接口

## 接口定位

`science-capability-registry` 提供科学能力定义。

它接收由 gateway 或 Skill 构造流程提出的 capability request，输出可被 `Sci_AI_OS` 绑定的 capability definition、benchmark definition、schema 和验证约束。

## INPUT

可接收：

- capability request
- scientific source evidence
- solver capability description
- benchmark source or benchmark request
- validation requirement
- schema extension request

## OUTPUT

必须输出一种或多种：

- capability definition
- capability card
- solver capability mapping
- numerical method description
- benchmark definition
- validation criteria
- input/output schema reference
- report or task record

## 调用关系

- `science-intelligence-gateway`：提出候选 registry placement 和待创建文件计划。
- `Sci_AI_OS`：在 Skill 执行前读取 capability definition 作为 science binding。
- RomAI / solver 后端：只通过 `Sci_AI_OS` 间接使用能力定义，不直接调用本仓库。

## 输出约束

- 能力定义必须描述科学对象、输入、输出、限制和验证方式。
- benchmark 必须描述科学验证问题，不应描述工具工作流。
- surrogate capability 只描述科学侧能力，不描述训练或推理 runtime。

## 禁止事项

- 禁止接收 raw source 作为系统入口。
- 禁止存放 Zotero、Bilibili、Codex、PDF parsing、GitHub mining 等工作流资产。
- 禁止执行 solver 或运行 RomAI。
- 禁止决定系统级 routing。
- 禁止把 workflow adapter 写成 science capability。
