# Fluent C01-C08 Seed Suite Static Readiness

日期：2026-07-02

## 结论

本轮把 Fluent 首批 C01-C08 从“教程来源扫描”推进到可测试的 seed-suite 静态契约。新增配置 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml`、schema `schemas/fluent_seed_suite.schema.json`、dry-run package `src/science_capability_registry/fluent/seed_suite/` 和 pytest 覆盖，目标是先冻结能力蒸馏边界，再进入本机 Fluent runtime。

## 覆盖范围

- exactly 8 个 seed：C01-C08。
- C01 已提升为 `package_skeleton_created` 并另有 runtime smoke evidence；C02-C08 仍为 `benchmark_candidate`。
- 每个 seed 均声明 problem definition、governing model、BC/IC、mesh/discretization、solver setup、input/output、benchmark source、validation criteria、perturbation axes、risks。
- 学习闭环固定为 `self_generated`、`official_replay`、`comparison`。
- dry-run 生成 `seed_suite_manifest.json`、`seed_cases.json`、`metrics.json`、`validation.json`、`validation_report.md`。

## Runtime 边界

本机已探测到 Ansys Fluent/Workbench 2025 R1/v251，但提交到仓库的 profile 不写入本机盘符路径。后续 runtime smoke 必须由本机环境变量或 ignored machine profile 注入 executable 路径，并先执行 C01 最小 batch journal。

## 不声明

- 不声明 Fluent solver runtime 已完成。
- 不声明官方 tutorial replay 等于 benchmark validation。
- 不声明 Workbench headless 自动化已经可用。
- 不提交 tutorial zip、解压内容、solver 输出或 license 相关本机状态。

## 下一道门

下一道门是 C01 `smoke`：用本机 Fluent 执行一个最小 standalone batch journal，产出 transcript、metrics、validation 和 report。C01 smoke 通过后，再按 C02 reference mapping、C03 mesh trend、C04 force/Cp、C05 transient VOF、C06 rotating/sliding、C07 thermal balance、C08 Workbench parameter 的顺序推进。
