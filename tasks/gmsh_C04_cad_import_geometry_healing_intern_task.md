# Gmsh C04 Intern Task: CAD Import Geometry Healing

## 目标

把 CAD import、OpenCASCADE healing 和 entity tracking 做成可复用能力，避免导入 STEP/BREP 后实体丢失、边界组错配或几何异常被隐藏。

## 范围

- 选择小型、可提交或可生成的 CAD smoke case。
- 先生成 `entity_map.json` 和 `healing_report.json`，再进入 mesh generation。
- 大型 CAD 和生成网格不得提交 Git。
- 当前已注册 static-ready catalog；真实 OpenCASCADE import 或 generated CAD runtime 仍需后续 smoke。

## 最小交付

1. 已完成：`schemas/gmsh_C04_cad_import_geometry_healing.schema.json`
2. 已完成：`configs/gmsh/cad_import_geometry_healing/baseline.yaml`
3. 已完成：static CAD import manifest、entity map、healing report、meshability summary
4. 已完成：unassigned face、missing rebinding group、duplicate/sliver entity negative tests
5. 已完成：`reports/gmsh_C04_cad_import_geometry_healing_static_readiness_2026-07-02.md`

## 验证标准

- imported/modified/deleted/new entity 必须可追踪。
- critical faces 未分配 physical group 必须失败。
- healing 操作必须来自 config，不得隐藏在 Python 常量里。
- mesh 生成成功不等于 CAD healing 正确，二者在报告中分开。

## 下一步

- 将 generated-smoke contract 替换或扩展为真实 OpenCASCADE import runtime。
- 对 imported/modified/deleted/new entity tag 做真实 parser。
- 继续禁止大型 CAD fixture 和生成网格进入 Git。
