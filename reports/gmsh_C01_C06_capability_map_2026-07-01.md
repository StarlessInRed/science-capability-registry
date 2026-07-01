# Gmsh C01-C06 Capability Map Closure

日期：2026-07-01

## 结论

OpenFOAM 首批 case-freeze 后，下一条资产路线转向 Gmsh。Gmsh 当前定位为 solver 前处理底座，优先覆盖 geometry、physical group、mesh refinement、CAD import、boundary-layer/size field 和 multi-solver export。

## 本轮新增

- `docs/02_four_repo_science_capability_chain.md`
- `software/gmsh/capability_map.md`
- `software/gmsh/assets/C02_boundary_physical_group_contract.yaml`
- `software/gmsh/assets/C03_mesh_refinement_quality_trend.yaml`
- `software/gmsh/assets/C04_cad_import_geometry_healing.yaml`
- `software/gmsh/assets/C05_boundary_layer_size_field_meshing.yaml`
- `software/gmsh/assets/C06_multi_solver_mesh_export_contract.yaml`
- `tasks/gmsh_C02_boundary_physical_group_contract_intern_task.md`
- `tasks/gmsh_C03_mesh_refinement_quality_trend_intern_task.md`
- `tasks/gmsh_C04_cad_import_geometry_healing_intern_task.md`
- `tasks/gmsh_C05_boundary_layer_size_field_meshing_intern_task.md`
- `tasks/gmsh_C06_multi_solver_mesh_export_contract_intern_task.md`

## 状态边界

C01 已有 package skeleton 和 OpenFOAM import/solve smoke。C02-C06 当前是 `benchmark_candidate`，不注册进 runtime catalog，因为还没有对应 schema/config/package/runtime evidence。

## 推荐执行顺序

1. C02 physical group contract。
2. C03 mesh refinement and quality trend。
3. C06 multi-solver export/import matrix。
4. C05 boundary-layer and size-field meshing。
5. C04 CAD import and geometry healing。

## 四仓链路

四仓职责按 `docs/02_four_repo_science_capability_chain.md` 固化：

- gateway 负责 raw input normalization 和 routing decision。
- capability registry 负责 science capability 正源。
- workflow registry 负责认知/信息处理 workflow 正源。
- `Sci_AI_OS` 负责 skill execution。

该报告不新增 runtime validation，只登记 Gmsh 首批能力路线和跨仓链路边界。
