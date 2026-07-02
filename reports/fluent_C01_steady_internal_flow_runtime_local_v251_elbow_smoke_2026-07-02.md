# Fluent C01 Steady Internal Flow Runtime Smoke

日期：2026-07-02

## 结论

Fluent C01 已完成本机 runtime smoke。该 smoke 使用本机 Ansys Fluent 2025 R1/v251 的 headless batch 模式读取 legacy `ch07/elbow` case/data，执行 bounded iteration，解析 residual 与 mass-flow report，并写出 case/data runtime artifact。验证结果为 `passed`。

## 运行配置

- config: `configs/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke.yaml`
- schema: `schemas/fluent_C01_steady_internal_flow_runtime.schema.json`
- package: `src/science_capability_registry/fluent/steady_internal_flow_runtime/`
- result root: `_results/fluent/steady_internal_flow_runtime/local_v251_elbow_smoke/`
- source role: legacy standalone runtime seed
- runtime boundary: executable 与 tutorial root 通过本机环境变量注入，仓库不固化本机盘符路径

## 指标

| metric | value |
| --- | ---: |
| Fluent return code | 0 |
| parsed residual rows | 4 |
| final iteration | 91 |
| max residual | 8.8669e-04 |
| mass-flow report count | 2 |
| inlet mass flow | 284.48006 kg/s |
| outlet mass flow | -284.47793 kg/s |
| selected net mass flow | 0.00213 kg/s |
| mass imbalance fraction | 7.48734375254824e-06 |

## 通过项

- case/data 读取成功。
- `2ddp -g -t1` headless batch 执行成功。
- legacy case 中指向旧路径的 report client 被显式停用后可继续迭代。
- residual threshold `1.0e-2` 通过。
- mass imbalance threshold `1.0e-3` 通过。
- `manifest.json`、`journal.jou`、`stdout.txt`、`stderr.txt`、`transcript.txt`、`metrics.json`、`validation.json`、`validation_report.md` 均已生成。

## 失败与修复记录

| failure | symptom | resolution |
| --- | --- | --- |
| Dimension profile mismatch | 使用 `3ddp` 读取 elbow case 时 Fluent 报 `File has wrong dimensions (2)`。 | 将 `dimension_precision` 放入 config，并为该 2D legacy case 使用 `2ddp`。 |
| Legacy report-client path | 旧 case 的 `surf-mon-1-rset` 指向历史本机盘符路径，迭代前要求确认。 | 在 config 中显式启用 `deactivate_invalid_report_clients`，journal 在 `/solve/iterate` 后回答 `yes`。 |
| Mass-flow TUI prompt | `/report/fluxes/mass-flow` 先询问是否选择所有边界，再询问是否写文件；若不回答，后续命令会被吞掉。 | journal 对 mass-flow 依次回答 `yes` 与 `no`，然后从 transcript 解析质量流量表。 |
| Empty stderr artifact | 成功运行时 `stderr.txt` 可能为空，非空检查会误判失败。 | artifact completeness 对 `stderr.txt` 只要求文件存在。 |

## 不声明

- 不声明 pressure-drop validation；C01 smoke 当前将 pressure drop 标记为 `not_extracted_in_c01_smoke`。
- 不声明 verification manual benchmark validation。
- 不声明官方 2025 R1 tutorial zip replay 已完成；本轮使用的是 legacy direct case/data 作为最小 runtime seed。
