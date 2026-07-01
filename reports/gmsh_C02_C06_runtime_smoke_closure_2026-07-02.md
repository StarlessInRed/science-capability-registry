# Gmsh C02-C06 Runtime Smoke Closure

> 2026-07-02 P1 update: 本报告是第一轮 runtime/replay closure；后续 `reports/gmsh_P1_runtime_promotion_closure_2026-07-02.md` 已补 fresh OpenFOAM import backed observation、generated STEP smoke 和 `meshio_fem_import`。本报告中的 replay/fixture 限制保留为历史边界。

## 结论

Gmsh C02-C06 已在 static-ready package skeleton 之外补齐一轮最小 runtime/replay smoke 证据。此轮不把所有能力提升为 benchmark validated；它的目的，是把真实 Gmsh Python API、已有 OpenFOAM import 证据、generated CAD smoke 和 multi-solver consumability fixture 串起来，证明下一阶段可以从 static contract 进入 runtime promotion。

## 运行结果

| 能力 | config | gate | result | 证据类型 |
| --- | --- | --- | --- | --- |
| C02 boundary physical group contract | `configs/gmsh/boundary_physical_group_contract/openfoam_import_replay_wsl_v2112.yaml` | smoke | passed | replay C01 OpenFOAM `gmshToFoam` import summary，验证 boundary names 和 polyMesh structural checks |
| C03 mesh refinement quality trend | `configs/gmsh/mesh_refinement_quality_trend/runtime_rectangle_channel_python_api.yaml` | smoke | passed | Gmsh Python API 真实生成 coarse/baseline/fine 三档 2D mesh |
| C04 CAD import geometry healing | `configs/gmsh/cad_import_geometry_healing/runtime_generated_occ_python_api.yaml` | smoke | passed | Gmsh/OpenCASCADE generated BREP export 后重新 open，并重绑定 inlet/outlet/wall |
| C05 boundary-layer size-field meshing | `configs/gmsh/boundary_layer_size_field_meshing/runtime_distance_threshold_python_api.yaml` | smoke | passed | Gmsh Python API Distance/Threshold size field 真实生成 near-wall refined mesh |
| C06 multi-solver mesh export contract | `configs/gmsh/multi_solver_mesh_export_contract/runtime_import_replay_and_msh_fixture.yaml` | smoke | passed | replay OpenFOAM import summary，并用 C03 `.msh` mesh summary 作为 FEM-oriented fixture parser |

## 关键指标

- C03 refinement smoke: coarse/baseline/fine 三档 node count 和 element count 均严格上升，`min_quality_proxy=0.8960255787859135`，`max_aspect_ratio_proxy=1.477478333621686`。
- C04 generated CAD smoke: imported entity count 为 9，surface count 为 1，critical groups 全部分配，unassigned entity 和 duplicate/sliver count 均为 0。
- C05 size-field smoke: near-wall element count 为 1706，min near-wall spacing 为 0.023635230211758396 m，min quality proxy 为 0.504866983075961。
- C06 consumability smoke: 两个 solver family target 通过，其中 OpenFOAM target 来自既有 `gmshToFoam` passed evidence，FEM-oriented target 来自 Gmsh `.msh` fixture parser；`successful_import_count=2`。

## 边界声明

- C02 当前是 downstream import replay，不是重新执行 OpenFOAM command。
- C03 是真实 Gmsh mesh generation，但还不是外部 solver accuracy validation。
- C04 是 generated BREP export/re-open smoke，不是复杂外部 STEP/BREP 文件 healing benchmark。
- C05 是 Distance/Threshold field runtime，不声称 CFD y+ 或 wall-function 合格。
- C06 的第二个 solver family 是 FEM-oriented `.msh` fixture parser，不声称 FEniCSx/CalculiX runtime 已执行。

## 下一步

Gmsh 现在可以进入 runtime promotion 阶段：把 C02 replay 变成 fresh OpenFOAM import command，把 C06 的 FEM fixture 变成真实 FEM import smoke，并把 C04 的 generated CAD smoke 扩展到可复现 STEP/BREP fixture。
