# Gmsh C05 Intern Task: Boundary-Layer And Size-Field Meshing

## 目标

建立 boundary-layer、distance field 或 threshold field 网格能力，让 near-wall、near-interface 或局部特征区域能够按配置获得更高分辨率。

## 范围

- 依赖 C02 的 wall/feature physical group。
- 输入包含 field type、target groups、first layer height、growth ratio、total thickness 和 quality thresholds。
- 不声称 CFD y+ 合格；y+ 属于下游 solver validation。
- 当前已注册 static-ready catalog；真实 Gmsh size-field generation 仍需后续 smoke。

## 最小交付

1. 已完成：`schemas/gmsh_C05_boundary_layer_size_field_meshing.schema.json`
2. 已完成：`configs/gmsh/boundary_layer_size_field_meshing/baseline.yaml`
3. 已完成：static size field manifest、boundary-layer summary 和 mesh-quality summary
4. 已完成：missing target group、impossible layer parameter、low-quality negative tests
5. 已完成：`reports/gmsh_C05_boundary_layer_size_field_meshing_static_readiness_2026-07-02.md`

## 验证标准

- target groups 缺失必须失败。
- first layer height、growth ratio、total thickness 必须为有效配置值。
- near-wall element count、spacing 和 observed growth ratio 必须进入 metrics。
- 全局 mesh quality 和 boundary-layer 质量分开报告。

## 下一步

- 接入真实 Gmsh `BoundaryLayer` 或 distance/threshold field generation。
- 将实际 near-wall spacing、observed growth ratio 和 global quality parser 输出喂给当前 validator。
- 与 OpenFOAM/FEM 的 y+、wall-function 或边界条件合法性保持解耦。
