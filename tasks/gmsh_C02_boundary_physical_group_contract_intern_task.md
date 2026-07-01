# Gmsh C02 Intern Task: Boundary Physical Group Contract

## 目标

把 Gmsh physical group 从“网格文件里的名字”提升为可验证的边界语义契约，确保下游 OpenFOAM、FEM 或多物理求解器导入时不靠猜测 patch/marker 角色。

## 范围

- 输入必须来自 schema/config，至少包含 group name、dimension、role、required/optional、downstream alias。
- 不做复杂几何生成；复用 C01 或一个最小矩形/通道 mesh。
- 当前已注册 static-ready catalog，先以 schema、manifest 和 negative validation 固定边界语义；真实 downstream import smoke 后才能提升 benchmark。

## 最小交付

1. 已完成：`schemas/gmsh_C02_boundary_physical_group_contract.schema.json`
2. 已完成：`configs/gmsh/boundary_physical_group_contract/baseline.yaml`
3. 已完成：`src/science_capability_registry/gmsh/boundary_physical_group_contract/`
4. 已完成：`tests/test_gmsh_c02_schema.py`、`tests/test_gmsh_c02_runner.py` 和 `tests/test_gmsh_c02_validation.py`
5. 已完成：`reports/gmsh_C02_boundary_physical_group_contract_static_readiness_2026-07-02.md`

## 验证标准

- 缺失 required group 必须失败。
- group 维度和 role 不匹配必须失败。
- downstream boundary map 必须覆盖 required groups。
- 报告必须区分 Gmsh group 生成成功和 solver BC 合法性。

## 下一步

- 用 C01 runtime 输出的 mesh/import 证据做 C02 downstream import smoke。
- 增加 renamed boundary 与 solver-specific alias 的负例。
- C02 仍不宣称真实 Gmsh mesh 生成或求解器 BC 正确性；这些归 C01 runtime、C06 export/import 或下游 solver 能力卡验证。
