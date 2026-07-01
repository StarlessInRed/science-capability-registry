# Gmsh Capability Map C01-C06

本文件记录 Gmsh 首批科学能力资产路线。Gmsh 位于 solver 前处理层，主要价值不是“画几何”，而是把几何语义、物理分组、网格质量、尺寸场、CAD 导入和多求解器导出变成可配置、可验证、可复用的能力。

## 首批能力

| C | capability slug | 主题 | 当前状态 | 关键验证量 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| C01 | `parametric_geometry_mesh_generation` | 参数化几何和基础网格生成 | `package_skeleton_created`。已有 schema/config/package、Gmsh Python API runtime、OpenFOAM `gmshToFoam` import smoke 和 `potentialFoam -writep` solve smoke。 | `.geo/.msh`、physical groups、element/node count、坐标有限性、OpenFOAM 导入/求解 smoke | mesh-quality perturbation、尺寸/几何扰动、solver-ready regression |
| C02 | `boundary_physical_group_contract` | physical group 和边界语义契约 | `package_skeleton_created`。已有 schema/config/package、dry-run contract artifacts、negative validation、registry static-ready dispatch，以及 OpenFOAM import replay smoke。 | physical group 名称/维度/角色、边界完整性、下游 BC 映射、缺失/重复/维度不匹配拒绝 | fresh downstream import command + renamed boundary negative case |
| C03 | `mesh_refinement_quality_trend` | 网格加密和质量趋势 | `package_skeleton_created`。已有 schema/config/package、dry-run refinement matrix、quality trend validation、registry static-ready dispatch，以及 Gmsh Python API refinement runtime smoke。 | element count、size field、quality proxy、Jacobian/angle/skew proxy、结果趋势 | actual perturbation matrix regression |
| C04 | `cad_import_geometry_healing` | CAD 导入、OpenCASCADE 几何修复和实体追踪 | `package_skeleton_created`。已有 schema/config/package、dry-run CAD import manifest、entity map、healing report、meshability validation、registry static-ready dispatch，以及 generated BREP export/re-open smoke。 | imported entities、healing operations、entity map、physical group preservation、nonmanifold/duplicate detection | external or generated STEP/BREP healing benchmark |
| C05 | `boundary_layer_size_field_meshing` | 边界层和尺寸场网格 | `package_skeleton_created`。已有 schema/config/package、dry-run size-field manifest、boundary-layer summary、near-wall metric validation、registry static-ready dispatch，以及 Distance/Threshold size-field runtime smoke。 | boundary-layer thickness/growth、distance/threshold fields、near-wall cell count、quality degradation | boundary-layer field runtime + downstream wall validation handoff |
| C06 | `multi_solver_mesh_export_contract` | 多求解器网格导出契约 | `package_skeleton_created`。已有 schema/config/package、dry-run export manifest、format matrix、solver import summary contract、registry static-ready dispatch，以及 OpenFOAM replay + FEM-oriented `.msh` fixture smoke。 | MSH2/MSH4/UNV/MED or solver import、boundary names、unit/orientation、downstream smoke | fresh OpenFOAM command + true FEM solver import smoke |

## 当前冻结标准

Gmsh C02-C06 均已进入 static-ready package skeleton，并具备一轮最小 runtime/replay smoke closure：

- capability card 通过 `schemas/capability_card.schema.json`。
- `software/gmsh/examples_index.md` 能发现来源和下一步 gate。
- 每个能力有可交给 intern 或 agent 的 task。
- C02-C06 均已注册进 `configs/registry/capability_catalog.json`，但只宣称 `static-readiness`。
- 后续 promotion 必须依次补真实 runtime smoke、integration evidence 或外部 double-v，不把 static contract 当成 runtime 成功。
- `reports/gmsh_C02_C06_runtime_smoke_closure_2026-07-02.md` 记录本轮最小 runtime/replay smoke；其中 C02/C06 的 OpenFOAM 部分为 replay evidence，C06 FEM target 为 `.msh` fixture parser，不等于真实 FEM solver runtime。

## 从 OpenFOAM 继承的失败学习

- 先声明 reference/source policy，再绑定数值 target。
- physical group、mesh quality 和 downstream import 是不同 gate，不能用一个 smoke 混称 benchmark validation。
- runtime profile 问题要和 capability 问题分开；例如 Gmsh mesh 生成通过，不代表 OpenFOAM/FEniCSx/CalculiX 导入都通过。
- 失败导入和低质量网格要进入 report/failure ledger，不删除、不静默通过。

## 推荐执行顺序

1. C02：补 downstream import smoke，把 static contract 和真实 solver import 分开验证。
2. C03：接入真实 Gmsh mesh quality summary，形成 refinement runtime smoke。
3. C06：用 C02+C03 的稳定 mesh 做真实多求解器 export/import smoke。
4. C05：接入真实 boundary-layer/size-field generation，服务 CFD wall-adjacent mesh。
5. C04：接入真实 CAD import/healing runtime，因为来源格式和几何异常更多，需要更强 failure ledger。

## 2026-07-02 P1 runtime promotion closure

- C02：已由本轮重新执行的 C01 OpenFOAM `gmshToFoam` import 支撑 boundary contract replay。
- C03：已接入真实 Gmsh Python API mesh quality summary，形成 refinement runtime smoke。
- C06：已由 OpenFOAM import observation 加 `meshio_fem_import` 形成两类 solver-family consumability smoke。
- C05：已接入 Distance/Threshold size-field runtime，服务 CFD wall-adjacent mesh；不声称 y+ 合格。
- C04：已接入 generated BREP 和 generated STEP import/re-open runtime；外部 CAD healing benchmark 仍是 promotion work。
- 证据入口：`reports/gmsh_P1_runtime_promotion_closure_2026-07-02.md`。
