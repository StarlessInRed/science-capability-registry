# Gmsh C06 Intern Task: Multi-Solver Mesh Export Contract

## 目标

把 Gmsh mesh export 从单一 `.msh` 文件扩展成多求解器导出/导入契约，验证 physical group、element count、unit/orientation 和 solver import smoke。

## 范围

- 复用 C02 boundary contract 和 C03 mesh quality summary。
- 首批至少包含 OpenFOAM 和一个 FEM-oriented target。
- 不做求解器物理结果验证，只做 mesh consumability。

## 最小交付

1. `schemas/gmsh_C06_multi_solver_mesh_export_contract.schema.json`
2. `configs/gmsh/multi_solver_mesh_export_contract/baseline.yaml`
3. export manifest、format matrix、solver import summary
4. boundary-name mismatch / element-count delta tests
5. `reports/gmsh_C06_multi_solver_mesh_export_contract_integration.md`

## 验证标准

- exported formats 必须来自 config。
- import smoke 必须记录成功/失败、boundary names、element counts 和 unit policy。
- 一个 solver import 通过只能证明 package skeleton；两个 solver family 通过后才考虑 benchmark_validated。
- solver-specific physics validation 必须链接到下游 solver capability，不在 C06 内部声称。
