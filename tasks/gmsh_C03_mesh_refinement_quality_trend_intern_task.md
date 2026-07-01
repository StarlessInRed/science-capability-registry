# Gmsh C03 Intern Task: Mesh Refinement Quality Trend

## 目标

建立 Gmsh 网格加密和质量趋势能力，让 mesh-size、algorithm、element order 的扰动能产生可解释、可验证的 element count 与 mesh quality 变化。

## 范围

- 复用 C02 的 physical group contract。
- 至少提供 baseline/coarse/fine 三档 refinement。
- 不做 solver 物理结果验证；只做 mesh quality 和 trend gate。
- 当前已注册 static-ready catalog；真实 Gmsh mesh quality parser 接入后再提升到 smoke/integration。

## 最小交付

1. 已完成：`schemas/gmsh_C03_mesh_refinement_quality_trend.schema.json`
2. 已完成：`configs/gmsh/mesh_refinement_quality_trend/baseline.yaml`
3. 已完成：static refinement matrix、mesh quality summary 和 trend validator
4. 已完成：low-quality、nonfinite coordinate 和 nonmonotonic trend negative tests
5. 已完成：`reports/gmsh_C03_mesh_refinement_quality_trend_static_readiness_2026-07-02.md`

## 验证标准

- refinement 后 node/element count 应按配置趋势变化。
- quality proxy 必须有限并高于阈值。
- 如果 refinement 导致质量下降，报告必须解释 tradeoff，不能静默通过。
- solver-ready claim 必须等 C06 import/export evidence。

## 下一步

- 将真实 Gmsh runtime 的 node/element count、quality proxy 和 coordinate finiteness 接入当前 validator。
- 增加 coarse/baseline/fine 三个实际 mesh 输出的 artifact completeness 检查。
- 保持 solver accuracy、solver import 和 physical boundary condition 合法性分别归 C06 或下游 solver 能力卡验证。
