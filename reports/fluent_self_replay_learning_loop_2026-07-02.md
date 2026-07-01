# Fluent Self-Generated vs Official Replay Learning Loop

日期：2026-07-02

## 目标

Fluent 能力构筑不以“跑通官方 zip”为终点。目标是让 registry 能够先自生成可解释算例，再用官方 tutorial zip 作为 replay 对照，通过差异学习 Fluent 的模型、边界、网格、单位、后处理和 runtime profile。

## 双路径设计

| 路径 | 作用 | 产物 |
| --- | --- | --- |
| `self_generated` | 从 config 生成 journal/setup，证明能力可参数化 | `journal.jou`、`metrics.json`、`validation.json` |
| `official_replay` | 解压官方 zip，复跑官方 case，作为对照组 | `official_manifest.json`、`official_metrics.json` |
| `comparison` | 比较自生成和官方 replay 的结果与设置差异 | `comparison.json`、`comparison_report.md` |

当前这三条路径已经进入 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml` 的静态契约；后续 runtime package 必须复用同一组 mode 名称，不再为每个案例临时发明新的 replay 语义。

## 差异分类

对比失败时必须分类，而不是直接调阈值：

- geometry mismatch
- mesh mismatch
- boundary-condition mismatch
- turbulence/model mismatch
- material/unit mismatch
- initialization or iteration mismatch
- transient time-step mismatch
- postprocess parser mismatch
- runtime profile or license mismatch
- tutorial/reference mismatch

## 8 个种子的学习职责

| C | 学习职责 |
| --- | --- |
| C01 | 训练 Fluent batch/journal/metrics 的最小闭环 |
| C02 | 训练 verification manual 到 benchmark target 的映射 |
| C03 | 训练 mesh/adaptation/convergence 差异解释 |
| C04 | 训练 force/Cp/reference CSV 对齐 |
| C05 | 训练 VOF boundedness、interface 和瞬态守恒 |
| C06 | 训练 moving/sliding zone 与时序 replay |
| C07 | 训练 heat flux、temperature range 和能量平衡 |
| C08 | 训练 Workbench project/parameter/result handoff |

## 不声明

- 官方 tutorial replay 通过不等于 benchmark validated。
- 自生成 case 与官方 case 完全一致不是必要目标；可解释、可分类、可复现才是目标。
- Workbench case 不混入 standalone Fluent batch gate。
