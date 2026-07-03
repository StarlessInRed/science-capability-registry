# Four-Repo Consumption Boundary - 2026-07-03

本报告记录 `science-capability-registry`、`science-intelligence-gateway`、`agent-workflow-registry`、`Sci_AI_OS` 四仓之间的能力消费边界。它是协作边界说明，不新增跨仓写入。

## Active Export Contract

`science-capability-registry` 当前最适合作为跨仓导出的 active contract 是：

- `configs/registry/capability_catalog.json`
- `schemas/capability_registry.schema.json`
- `reports/evidence_index.yaml`

其他仓应消费 catalog 中的 `capability_id`、asset/schema/config 路径、`dispatch_status`、`current_gate`、`primary_evidence_id` 和 `result_contract`，而不是复制完整 asset card 或重新定义科学能力。

## Consumer Boundaries

| repo | consumer role | boundary |
| --- | --- | --- |
| `science-intelligence-gateway` | source intake and routing | May reference `capability_catalog_ref`; should not directly write SCR assets. |
| `agent-workflow-registry` | workflow routing and review handoff | May record routing decisions and review tasks; secondary registry remains review-only. |
| `Sci_AI_OS` | scientific CI / replay consumer | May reference frozen benchmark manifests and replay evidence; should not redefine SCR capability ontology. |

## Do Not Cross

- Do not copy SCR capability cards or benchmark manifests into other repos as duplicated truth.
- Do not let gateway/AWR directly create or mutate SCR canonical assets.
- Do not place raw source mining output, large solver runtime output, `_results/`, or local absolute paths into cross-repo contracts.
- Do not treat Sci_AI_OS replay evidence as a replacement for SCR benchmark promotion.

## Current Boundary

This closes the routing-level task: the export tuple and consumer responsibilities are explicit. Actual cross-repo implementation should happen in the consumer repos in later dedicated changes.
