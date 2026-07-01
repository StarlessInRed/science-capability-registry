# Gmsh Capability Map C01-C06

本文件记录 Gmsh 首批科学能力资产路线。Gmsh 位于 solver 前处理层，主要价值不是“画几何”，而是把几何语义、物理分组、网格质量、尺寸场、CAD 导入和多求解器导出变成可配置、可验证、可复用的能力。

## 首批能力

| C | capability slug | 主题 | 当前状态 | 关键验证量 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| C01 | `parametric_geometry_mesh_generation` | 参数化几何和基础网格生成 | `package_skeleton_created`。已有 schema/config/package、Gmsh Python API runtime、OpenFOAM `gmshToFoam` import smoke 和 `potentialFoam -writep` solve smoke。 | `.geo/.msh`、physical groups、element/node count、坐标有限性、OpenFOAM 导入/求解 smoke | mesh-quality perturbation、尺寸/几何扰动、solver-ready regression |
| C02 | `boundary_physical_group_contract` | physical group 和边界语义契约 | `benchmark_candidate`。资产卡和任务已建立。 | physical group 名称/维度/角色、边界完整性、下游 BC 映射、缺失/重命名拒绝 | schema + manifest validator + OpenFOAM/FEM boundary mapping smoke |
| C03 | `mesh_refinement_quality_trend` | 网格加密和质量趋势 | `benchmark_candidate`。资产卡和任务已建立。 | element count、size field、quality proxy、Jacobian/angle/skew proxy、结果趋势 | refinement matrix config + quality parser + regression thresholds |
| C04 | `cad_import_geometry_healing` | CAD 导入、OpenCASCADE 几何修复和实体追踪 | `benchmark_candidate`。资产卡和任务已建立。 | imported entities、healing operations、entity map、physical group preservation、nonmanifold/duplicate detection | STEP/BREP import smoke + entity-map report |
| C05 | `boundary_layer_size_field_meshing` | 边界层和尺寸场网格 | `benchmark_candidate`。资产卡和任务已建立。 | boundary-layer thickness/growth、distance/threshold fields、near-wall cell count、quality degradation | size-field config schema + boundary-layer validation matrix |
| C06 | `multi_solver_mesh_export_contract` | 多求解器网格导出契约 | `benchmark_candidate`。资产卡和任务已建立。 | MSH2/MSH4/UNV/MED or solver import、boundary names、unit/orientation、downstream smoke | OpenFOAM/FEniCSx/CalculiX export/import matrix |

## 当前冻结标准

Gmsh C02-C06 当前只要求候选资产完整：

- capability card 通过 `schemas/capability_card.schema.json`。
- `software/gmsh/examples_index.md` 能发现来源和下一步 gate。
- 每个能力有可交给 intern 或 agent 的 task。
- 不注册进 `configs/registry/capability_catalog.json`，直到对应 schema/config/package/runtime evidence 存在。

## 从 OpenFOAM 继承的失败学习

- 先声明 reference/source policy，再绑定数值 target。
- physical group、mesh quality 和 downstream import 是不同 gate，不能用一个 smoke 混称 benchmark validation。
- runtime profile 问题要和 capability 问题分开；例如 Gmsh mesh 生成通过，不代表 OpenFOAM/FEniCSx/CalculiX 导入都通过。
- 失败导入和低质量网格要进入 report/failure ledger，不删除、不静默通过。

## 推荐执行顺序

1. C02：先把 boundary/physical group contract 做成 schema 和 manifest validator。
2. C03：在 C02 边界契约稳定后做 refinement/quality matrix。
3. C06：用 C02+C03 的稳定 mesh 做多求解器 export/import smoke。
4. C05：补 boundary-layer/size-field，服务 CFD wall-adjacent mesh。
5. C04：最后做 CAD import/healing，因为来源格式和几何异常更多，需要更强 failure ledger。
