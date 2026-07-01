# Gmsh P1 Runtime Promotion Closure

日期：2026-07-02

## 结论

Gmsh P1 在本机 smoke 范围内已完成：C02 的 OpenFOAM 边界语义 replay 已由本轮重新执行的 C01 `gmshToFoam` import 支撑，C04 已从 BREP 扩展到 generated STEP/BREP CAD import smoke，C06 已从 `.msh` summary fixture 提升为 `meshio` FEM importer smoke。

这不是 benchmark promotion：Gmsh C02-C06 仍保持 `package_skeleton_created`，因为它们验证的是 mesh/format/contract consumability，不验证下游 solver 物理正确性。

## P1 任务闭环

| 项 | 结果 | 证据 | 仍不声明 |
| --- | --- | --- | --- |
| C02 fresh downstream import handoff | passed | 先重新运行 `configs/gmsh/parametric_geometry_mesh_generation/openfoam_import_wsl_v2112.yaml`，再由 `configs/gmsh/boundary_physical_group_contract/openfoam_import_replay_wsl_v2112.yaml` 消费新鲜 `downstream_import_summary.json` | C02 自身没有生成新几何；它验证边界 contract 消费，不验证 CFD 物理 |
| C04 generated STEP/BREP CAD smoke | passed | `configs/gmsh/cad_import_geometry_healing/runtime_generated_step_python_api.yaml` 和既有 BREP smoke 均可导入并重绑定 inlet/outlet/wall | 外部复杂 CAD healing benchmark |
| C06 multi-solver import smoke | passed | OpenFOAM import observation + `meshio_fem_import` 读取 C03 fine `.msh`，边界 cell sets 和单元计数通过 | FEniCSx/CalculiX solver runtime |
| C05 size-field runtime | retained | `runtime_distance_threshold_python_api.yaml` 真实生成 Distance/Threshold near-wall refined mesh | CFD y+ band 或 wall-function 合格 |

## 关键运行结果

- Fresh Gmsh C01 OpenFOAM import：Gmsh 重新生成 3D mesh，`gmshToFoam` import `status=passed`。
- C02 boundary contract replay：`validation.passed=true`，`role_mapping_coverage=1.0`。
- C04 generated STEP smoke：`imported_entity_count=9`，`imported_surface_count=1`，`unassigned_entity_count=0`。
- C06 meshio FEM import：两个 solver-family target 通过，`successful_import_count=2`，target 为 `openfoam_gmshToFoam` 和 `meshio_msh_fem_import`。

## 对 Fluent 和 MATLAB 驱动 COMSOL 的迁移意义

- Fluent import 应复用 C02 的 boundary role contract 和 C06 的 solver-family import summary，而不是直接把 `.msh` 文件交给 Fluent 后只看是否打开成功。
- COMSOL 通过 MATLAB 驱动时，应把 mesh import、physics assignment、study run、postprocess validation 拆成不同 gate。Gmsh C06 的经验说明：mesh importer 通过不等于 FEM physics validation。
- CAD/geometry 前处理必须保留 entity-map 和 physical-group rebinding 证据。C04 的 STEP smoke 可作为 COMSOL/Fluent CAD 输入链的最小 fixture 模板。

## 剩余边界

- `meshio` 是轻量 FEM mesh importer，不是 FEniCSx 或 CalculiX runtime。
- 当前 CAD fixture 是 generated STEP/BREP，不覆盖外部 CAD 中常见的断边、小面、非流形或单位混乱问题。
- C02/C06 的 OpenFOAM 部分依赖本机 WSL OpenFOAM.com v2112 路径可用；这是本地 smoke，不是跨机器 double-v。
