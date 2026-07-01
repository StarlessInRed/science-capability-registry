# Gmsh C05 Boundary-Layer Size-Field Meshing Static Readiness

## 结论

Gmsh C05 已完成 static-readiness 闭环：schema、baseline config、package entrypoint、dry-run size-field manifest、boundary-layer summary、mesh-quality summary、negative validation、catalog dispatch 和 evidence index 均已建立。

本报告不声称真实 Gmsh boundary-layer 或 distance/threshold field 已生成，也不声称 CFD y+ 或 wall-function 合格。C05 当前证明的是：field type、target physical groups、first-layer height、growth ratio、total thickness、near-wall metrics 和 quality thresholds 可以被结构化配置声明，并在 solver validation 前自动拒绝明显错误。

## 本轮交付

- `schemas/gmsh_C05_boundary_layer_size_field_meshing.schema.json`
- `configs/gmsh/boundary_layer_size_field_meshing/baseline.yaml`
- `src/science_capability_registry/gmsh/boundary_layer_size_field_meshing/`
- `tests/test_gmsh_c05_schema.py`
- `tests/test_gmsh_c05_runner.py`
- `tests/test_gmsh_c05_validation.py`
- `configs/registry/capability_catalog.json` 中的 `meshing.gmsh.boundary_layer_size_field_meshing`

## 验证范围

- baseline config 必须通过 C05 JSON Schema。
- runner dry-run 必须写出 `size_field_manifest.json`、`boundary_layer_summary.json`、`mesh_quality_summary.json`、`manifest.json`、`metrics.json`、`validation.json` 和 `validation_report.md`。
- target groups 必须覆盖 required wall/feature group。
- first-layer height、growth ratio、total thickness 和 far-field size 必须形成有效配置。
- near-wall element count、min spacing、observed growth ratio 和 min quality proxy 必须通过阈值。
- validation report 必须明确区分 boundary-layer metrics、global mesh quality 和 downstream CFD y+。

## 当前状态

- `card_status`: `review`
- `benchmark_status`: `package_skeleton_created`
- `dispatch_status`: `static_ready`
- `current_gate`: `static-readiness`

## 未验证风险

- 尚未执行真实 Gmsh boundary-layer 或 distance/threshold field generation。
- 尚未从实际 mesh 中解析 near-wall spacing、observed growth ratio 或 quality proxy。
- 尚未连接 downstream solver y+ 或 wall-function validation。

## 下一步

把当前 static contract 接到真实 Gmsh size-field runtime，再把 solver-facing wall validation 留给 OpenFOAM 或其他下游 solver 能力卡。
