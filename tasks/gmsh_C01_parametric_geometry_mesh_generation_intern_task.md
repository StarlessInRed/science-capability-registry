# Gmsh C01 Intern Task: Parametric Geometry And Mesh Generation

## 目标

把 Gmsh 官方 reference manual 与 `t1.geo` tutorial 中的参数化几何、physical group 和 mesh 生成能力，转化为本仓库可复用、可配置、可验证的网格生成能力。

## 范围

- 输入必须来自 JSON/YAML config，不允许把几何尺寸、physical group 名称、mesh-size 控制藏在 CLI 参数或脚本常量里。
- 第一版目标是生成一个明确的 `.geo`、`.msh`、`mesh_summary.json`、`validation.json` 和 `validation_report.md`。
- benchmark_status 在没有本地 runtime 和下游导入 smoke 前保持 `benchmark_candidate`。

## 最小交付

1. `schemas/gmsh_C01_parametric_geometry_mesh_generation.schema.json`
2. `configs/gmsh/parametric_geometry_mesh_generation/baseline.yaml`
3. `src/science_capability_registry/gmsh/parametric_geometry_mesh_generation/` package skeleton
4. Gmsh runtime profile 或可复用执行配置
5. mesh quality parser 和 validation gate
6. pytest 覆盖 schema、dry-run manifest、physical group 完整性、mesh quality 和 artifact completeness

## 验证标准

- 所有 required physical groups 必须存在，并且名称与 config 完全一致。
- mesh 文件、summary、validation 和报告必须生成。
- element count 必须为正，坐标必须有限。
- mesh quality 指标必须可解析；低质量网格应触发失败而不是静默通过。
- 下游 solver import 或格式转换 smoke 未完成前，不得把能力提升为 `benchmark_validated`。
