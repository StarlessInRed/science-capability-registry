# Gmsh C02 Intern Task: Boundary Physical Group Contract

## 目标

把 Gmsh physical group 从“网格文件里的名字”提升为可验证的边界语义契约，确保下游 OpenFOAM、FEM 或多物理求解器导入时不靠猜测 patch/marker 角色。

## 范围

- 输入必须来自 schema/config，至少包含 group name、dimension、role、required/optional、downstream alias。
- 不做复杂几何生成；复用 C01 或一个最小矩形/通道 mesh。
- 当前不注册 runtime catalog，先完成 schema、manifest 和 negative validation。

## 最小交付

1. `schemas/gmsh_C02_boundary_physical_group_contract.schema.json`
2. `configs/gmsh/boundary_physical_group_contract/baseline.yaml`
3. `src/science_capability_registry/gmsh/boundary_physical_group_contract/`
4. `tests/test_gmsh_c02_schema.py` 和 `tests/test_gmsh_c02_validation.py`
5. `reports/gmsh_C02_boundary_physical_group_contract_static_readiness.md`

## 验证标准

- 缺失 required group 必须失败。
- group 维度和 role 不匹配必须失败。
- downstream boundary map 必须覆盖 required groups。
- 报告必须区分 Gmsh group 生成成功和 solver BC 合法性。
