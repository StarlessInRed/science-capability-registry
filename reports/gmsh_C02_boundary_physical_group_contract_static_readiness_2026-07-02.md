# Gmsh C02 Boundary Physical Group Contract Static Readiness

## 结论

Gmsh C02 已完成 static-readiness 闭环：schema、baseline config、package entrypoint、dry-run manifest、negative validation、catalog dispatch 和 evidence index 均已建立。

本报告不声称 Gmsh mesh 生成成功，也不声称 OpenFOAM、FEniCSx 或 CalculiX 已成功导入边界。C02 当前证明的是：physical group 名称、维度、角色、required 状态、downstream alias 和 solver-facing boundary map 可以被结构化配置声明，并在 solver runtime 之前自动拒绝明显错误。

## 本轮交付

- `schemas/gmsh_C02_boundary_physical_group_contract.schema.json`
- `configs/gmsh/boundary_physical_group_contract/baseline.yaml`
- `src/science_capability_registry/gmsh/boundary_physical_group_contract/`
- `tests/test_gmsh_c02_schema.py`
- `tests/test_gmsh_c02_runner.py`
- `tests/test_gmsh_c02_validation.py`
- `configs/registry/capability_catalog.json` 中的 `meshing.gmsh.boundary_physical_group_contract`

## 验证范围

- baseline config 必须通过 C02 JSON Schema。
- runner dry-run 必须写出 `physical_group_map.json`、`boundary_contract.json`、`manifest.json`、`metrics.json`、`validation.json` 和 `validation_report.md`。
- 缺失 required group 必须失败。
- 角色和几何维度不匹配必须失败。
- duplicate physical group name 必须失败。
- downstream boundary map 缺少 required role 必须失败。
- validation report 必须明确区分 boundary contract 静态有效性、Gmsh mesh generation、下游 solver import 和 solver BC 合法性。

## 当前状态

- `card_status`: `review`
- `benchmark_status`: `package_skeleton_created`
- `dispatch_status`: `static_ready`
- `current_gate`: `static-readiness`

## 未验证风险

- 尚未把 C01 runtime mesh 的实际 physical group 输出重新喂给 C02 做 downstream import smoke。
- 尚未证明边界名在 OpenFOAM 之外的 solver family 中保持语义一致。
- 尚未处理真实 CAD/import 场景中的 entity rename、entity merge 或 physical group 丢失。

## 下一步

用 C02 contract 作为 C03、C05、C06 的边界语义底座；在 C06 多求解器导出前，先补一个基于 C01 OpenFOAM import artifact 的 C02 downstream import smoke。
