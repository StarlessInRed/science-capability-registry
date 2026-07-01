# Gmsh C03 Intern Task: Mesh Refinement Quality Trend

## 目标

建立 Gmsh 网格加密和质量趋势能力，让 mesh-size、algorithm、element order 的扰动能产生可解释、可验证的 element count 与 mesh quality 变化。

## 范围

- 复用 C02 的 physical group contract。
- 至少提供 baseline/coarse/fine 三档 refinement。
- 不做 solver 物理结果验证；只做 mesh quality 和 trend gate。

## 最小交付

1. `schemas/gmsh_C03_mesh_refinement_quality_trend.schema.json`
2. `configs/gmsh/mesh_refinement_quality_trend/{baseline,coarse,fine}.yaml`
3. mesh quality parser 和 `refinement_matrix.csv`
4. low-quality 和 nonfinite coordinate negative tests
5. `reports/gmsh_C03_mesh_refinement_quality_trend_integration.md`

## 验证标准

- refinement 后 node/element count 应按配置趋势变化。
- quality proxy 必须有限并高于阈值。
- 如果 refinement 导致质量下降，报告必须解释 tradeoff，不能静默通过。
- solver-ready claim 必须等 C06 import/export evidence。
