# Gmsh C06 Multi-Solver Mesh Export Contract Static Readiness

## 结论

Gmsh C06 已完成 static-readiness 闭环：schema、baseline config、package entrypoint、dry-run export manifest、format matrix、solver import summary、negative validation、catalog dispatch 和 evidence index 均已建立。

本报告不声称任何 downstream solver import command 已执行，也不声称 OpenFOAM、FEniCSx 或 CalculiX 已成功消费网格。C06 当前证明的是：source mesh、C02 boundary contract、C03 quality contract、solver target、export format、unit policy、orientation policy、boundary-name expectation 和 element-count delta 约束可以被结构化配置声明并自动验证。

## 本轮交付

- `schemas/gmsh_C06_multi_solver_mesh_export_contract.schema.json`
- `configs/gmsh/multi_solver_mesh_export_contract/baseline.yaml`
- `src/science_capability_registry/gmsh/multi_solver_mesh_export_contract/`
- `tests/test_gmsh_c06_schema.py`
- `tests/test_gmsh_c06_runner.py`
- `tests/test_gmsh_c06_validation.py`
- `configs/registry/capability_catalog.json` 中的 `meshing.gmsh.multi_solver_mesh_export_contract`

## 验证范围

- baseline config 必须通过 C06 JSON Schema。
- runner dry-run 必须写出 `export_manifest.json`、`format_matrix.csv`、`solver_import_summary.json`、`manifest.json`、`metrics.json`、`validation.json` 和 `validation_report.md`。
- export target 必须覆盖 OpenFOAM-oriented CFD 和 FEM-oriented target。
- required boundary names 必须出现在每个 target 的 expectation 中。
- unit scale 必须在当前 contract 中保持一致。
- orientation policy 必须要求 positive orientation。
- element-count delta fraction 必须保持在静态阈值内。
- validation report 必须明确区分 export/import contract 和真实 import command execution。

## 当前状态

- `card_status`: `review`
- `benchmark_status`: `package_skeleton_created`
- `dispatch_status`: `static_ready`
- `current_gate`: `static-readiness`

## 未验证风险

- 尚未执行 OpenFOAM `gmshToFoam` replay。
- 尚未执行 FEM-oriented solver import smoke。
- 尚未从真实 import artifact 中比较 boundary names、element counts、orientation 或 unit conversion。

## 下一步

用 C01/C02/C03 的真实 runtime 输出替换当前 static target expectation，先完成 OpenFOAM replay，再补一个 FEM-oriented fixture 或 runtime import smoke。
