# Gmsh C04 Intern Task: CAD Import Geometry Healing

## 目标

把 CAD import、OpenCASCADE healing 和 entity tracking 做成可复用能力，避免导入 STEP/BREP 后实体丢失、边界组错配或几何异常被隐藏。

## 范围

- 选择小型、可提交或可生成的 CAD smoke case。
- 先生成 `entity_map.json` 和 `healing_report.json`，再进入 mesh generation。
- 大型 CAD 和生成网格不得提交 Git。

## 最小交付

1. `schemas/gmsh_C04_cad_import_geometry_healing.schema.json`
2. `configs/gmsh/cad_import_geometry_healing/baseline.yaml`
3. CAD import manifest、entity map、healing report
4. unassigned face / duplicate entity negative tests
5. `reports/gmsh_C04_cad_import_geometry_healing_smoke.md`

## 验证标准

- imported/modified/deleted/new entity 必须可追踪。
- critical faces 未分配 physical group 必须失败。
- healing 操作必须来自 config，不得隐藏在 Python 常量里。
- mesh 生成成功不等于 CAD healing 正确，二者在报告中分开。
