# Gmsh C05 Intern Task: Boundary-Layer And Size-Field Meshing

## 目标

建立 boundary-layer、distance field 或 threshold field 网格能力，让 near-wall、near-interface 或局部特征区域能够按配置获得更高分辨率。

## 范围

- 依赖 C02 的 wall/feature physical group。
- 输入包含 field type、target groups、first layer height、growth ratio、total thickness 和 quality thresholds。
- 不声称 CFD y+ 合格；y+ 属于下游 solver validation。

## 最小交付

1. `schemas/gmsh_C05_boundary_layer_size_field_meshing.schema.json`
2. `configs/gmsh/boundary_layer_size_field_meshing/baseline.yaml`
3. size field manifest 和 boundary-layer summary
4. missing target group / impossible layer parameter negative tests
5. `reports/gmsh_C05_boundary_layer_size_field_meshing_smoke.md`

## 验证标准

- target groups 缺失必须失败。
- first layer height、growth ratio、total thickness 必须为有效配置值。
- near-wall element count、spacing 和 observed growth ratio 必须进入 metrics。
- 全局 mesh quality 和 boundary-layer 质量分开报告。
