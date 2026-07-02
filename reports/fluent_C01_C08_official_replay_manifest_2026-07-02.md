# Fluent C01-C08 Official Replay Manifest

日期：2026-07-02

## 结论

新增 Fluent C01-C08 官方/legacy/Workbench/verification source manifest 支撑层。它只读 zip central directory、legacy source directory 和 reference PDF 文件，不解压、不启动 Fluent、不启动 Workbench。该层的作用是把“哪些来源可作为 replay、哪些只有 mesh、哪些含 reference CSV、哪些必须走 Workbench”固化为可审计 artifact。

本机扫描通过：9 个来源包全部 readable，识别 24 个 source entries，覆盖 8 个 capability bindings，expected entry classes 缺失数为 0。

## 产物

- config: `configs/fluent/official_replay_manifest/c01_c08_sources.yaml`
- schema: `schemas/fluent_official_replay_manifest.schema.json`
- package: `src/science_capability_registry/fluent/official_replay_manifest/`
- tests: `tests/test_fluent_replay_manifest_schema.py`、`tests/test_fluent_replay_manifest_runner.py`、`tests/test_fluent_replay_manifest_validation.py`
- runtime evidence root: `_results/fluent/official_replay_manifest/c01_c08_sources/`

## Capability Bindings

| C | primary source | first action |
| --- | --- | --- |
| C01 | legacy `Fluent_tutorial_case/ch07/elbow` | continue batch smoke; add pressure-drop only after transcript evidence |
| C02 | verification manual | self-generate VMFL005 pipe case |
| C03 | `fluent_adaptation.zip` | define refinement/adaptation levels |
| C04 | `fluent_aero_tutorial.zip` | parse reference CSV, then short aero replay |
| C05 | `vof.zip` | mesh/setup manifest before transient solver |
| C06 | `sliding_mesh.zip` plus `single_rotating.zip` | moving-zone candidate manifest |
| C07 | `2d_heat_exchanger_optimizer.zip` | case/data replay and heat-rate extraction |
| C08 | `workbench_parameter.zip` | WBPZ parameter/project manifest |

## Manifest Metrics

| metric | value |
| --- | ---: |
| package count | 9 |
| readable package count | 9 |
| source entry count | 24 |
| binding count | 8 |
| missing expected entry classes | 0 |
| case entries | 4 |
| data entries | 2 |
| mesh entries | 8 |
| reference CSV entries | 3 |
| Workbench archive entries | 1 |

## 不声明

- 不声明 C04-C08 已 runtime smoke。
- 不声明 tutorial replay 等于 benchmark validation。
- 不声明 mesh-only zip 可直接 solver replay。
- 不声明 Workbench archive 可由 standalone Fluent batch 消费。
