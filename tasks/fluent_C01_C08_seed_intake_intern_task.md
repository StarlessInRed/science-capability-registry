# Fluent C01-C08 Seed Intake Intern Task

## 任务目标

将 Fluent 官方 tutorial、verification manual、Workbench tutorial 与 legacy case source 转换为前 8 个能力 seed。第一阶段只要求完成 source intake、能力地图、runtime profile 和 replay-learning contract；不要提交大型解压数据，也不要把 tutorial replay 宣称为 benchmark validation。

## 交付物

1. 更新 `software/fluent/capability_map.md`。
2. 更新 `software/fluent/examples_index.md`。
3. 为 C01-C08 维护 capability card，并通过 `schemas/capability_card.schema.json`。
4. 维护 `configs/fluent/runtime_profiles/local_fluent_preflight.yaml`。
5. 维护 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml` 与 `schemas/fluent_seed_suite.schema.json`。
6. 维护 seed-suite dry-run，产出 manifest、metrics、validation 和静态验收报告。
7. 完成 source intake 后，不提交大型解压数据或 runtime evidence 到 Git。

## 验收标准

- 每个 seed 都说明来源角色、输入、输出、validation gate 和不应声明的边界。
- Tutorial Guide、Verification Manual、Workbench Tutorial 的证据角色必须分开。
- Fluent runtime path 必须通过 config/profile 注入，不允许写入源码。
- 失败必须记录为 runtime-profile、license/module、reference mismatch、parser failure 或 source-role boundary 等可复盘类型。

## Failure Ledger Requirement

所有 Fluent C01-C08 的 source-role、runtime-profile、parser、setup、license/module 或 validation failure，都必须登记到 `reports/fluent_failure_ledger.yaml`，并受 `schemas/fluent_failure_ledger.schema.json` 与 `tests/test_fluent_failure_ledger.py` 保护。不要把对话记忆作为唯一的 canonical failure evidence。
