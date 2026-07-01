# Fluent C01-C08 Seed Intake Intern Task

## 任务目标

把 Fluent 官方 tutorial、verification manual、Workbench tutorial 和 legacy case source 转化为首批 8 个能力种子。第一阶段只要求 source intake、能力地图、runtime profile 和 replay-learning contract，不要求批量运行所有 zip。

## 必交付

1. 更新 `software/fluent/capability_map.md`。
2. 更新 `software/fluent/examples_index.md`。
3. 为 C01-C08 保持 capability card 可通过 `schemas/capability_card.schema.json`。
4. 维护 `configs/fluent/runtime_profiles/local_fluent_preflight.yaml`。
5. 维护 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml` 与 `schemas/fluent_seed_suite.schema.json`。
6. 运行 seed-suite dry-run，生成 manifest/metrics/validation 的静态闭环。
7. 运行 source intake 后，不把大型解压内容提交到 Git。

## 接受标准

- 每个 seed 都能说明来源、物理类型、输入、输出、validation gate 和不声明边界。
- Tutorial Guide、Verification Manual、Workbench Tutorial 的证据角色必须分开。
- Fluent runtime 路径必须通过 config/profile 注入，不允许写入源码。
- 失败必须记录为 runtime-profile、license、module、reference mismatch 或 parser failure。
