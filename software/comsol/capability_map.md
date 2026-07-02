# COMSOL MATLAB Driver Capability Map C01-C06

本文件记录 COMSOL Multiphysics 通过 LiveLink for MATLAB 进行驱动时，首批 C01-C06 科学能力资产的范围、证据来源、验证门槛和未闭环边界。

这里的目标不是让用户学习 COMSOL Desktop 操作，而是把 MATLAB 脚本、COMSOL API、模型文件、求解、结果导出和验证标准组织成可复用能力资产。

## Source Boundary

| source | role | current use |
| --- | --- | --- |
| COMSOL LiveLink for MATLAB product page | Product capability evidence | Confirms MATLAB can drive COMSOL modeling, meshing, solving, parametric studies, and result extraction through the COMSOL API. |
| LiveLink for MATLAB User's Guide | API and command-line evidence | Candidate source for `mphstart`, `mphopen`, `mphsave`, `mphinterp`, solver execution, and client/server startup contracts. |
| COMSOL Application Libraries | Benchmark/source candidate | Future source for official `.mph` examples once a local COMSOL installation and library root are configured. |
| Self-generated MATLAB scripts | Reproducible driver source | First local static/preflight route before any official model replay is claimed. |

## C01-C06 Capability Split

| C | capability slug | role | preferred source | validation focus | first gate |
| --- | --- | --- | --- | --- | --- |
| C01 | `matlab_server_bridge_runtime` | MATLAB-COMSOL server/session bridge and minimal roundtrip | LiveLink API and self-generated minimal model | executable profile, server/session connection, model open/create, finite scalar extraction | package skeleton + preflight runner; runtime smoke pending |
| C02 | `model_construction_api_contract` | Build a COMSOL model from MATLAB-controlled API calls | generated heat/PDE model contract | model tree tags, parameters, material, geometry, mesh, study object creation | static-readiness |
| C03 | `geometry_mesh_import_contract` | Geometry, mesh, import, and selection-map readiness | generated geometry first, official model later | entity counts, selections, boundary role map, mesh/import status | static-readiness |
| C04 | `physics_boundary_assignment_contract` | Physics interface, material, boundary, and initial-condition assignment | C02 generated model or official small model | BC/IC completeness, units, physics feature tags, rejection of missing assignments | static-readiness |
| C05 | `study_run_solver_smoke` | Study execution, solver status, and benchmark-ready result state | C02/C04 generated model | solver completion, convergence/status, final datasets, nonempty result state | static-readiness then smoke |
| C06 | `result_extraction_postprocess_validation` | MATLAB-side extraction, canonical exports, and downstream consumability | solved C05 result | `mphglobal`/`mphinterp`/tables, units, finite values, CSV/JSON handoff | static-readiness |

## Why C01-C06

C01-C06 是 MATLAB 驱动 COMSOL 的六个基础动作面，不是六个固定物理题：

- C01 建立 runtime envelope。
- C02 证明 MATLAB 能构造可审查的模型对象。
- C03 处理几何、mesh、selection 和 import 这些最常见工程失败点。
- C04 把 physics/material/BC/IC assignment 从模型构建中拆出来，防止“能建几何但物理不完整”。
- C05 单独验证 study/solver run，不把启动、建模、求解和验证混成一个 gate。
- C06 证明结果能被 registry、Python、报告或后续 agent workflow 消费。

后续具体物理 benchmark，例如热传导、Joule heating、瞬态热、流固或优化循环，都应该挂在这些动作面之上。

## Current Boundary

本机当前未在 PATH 或常见安装目录中发现 MATLAB/COMSOL 命令，因此本轮只声明 capability-map static-readiness 与 C01 package skeleton/preflight runner，不声明 C01 runtime smoke、C02 benchmark validation 或 COMSOL solver execution。

后续进入 runtime 前必须配置：

- `MATLAB_EXE`: MATLAB executable path.
- `COMSOL_EXE` or `COMSOL_BIN`: COMSOL command/client path.
- `COMSOL_MPHSERVER_BIN`: COMSOL server path when server mode is used.
- `COMSOL_MLI_DIR`: LiveLink for MATLAB API path if not auto-discoverable.
- `COMSOL_APPLICATION_LIBRARY_ROOT`: optional official model library root.

## Next Gates

1. Configure C01 runtime profile and promote from preflight-only to MATLAB LiveLink smoke.
2. C02 model construction API contract.
3. C03 geometry/mesh/selection manifest.
4. C04 physics/material/boundary assignment contract.
5. C05 study-run solver smoke.
6. C06 result extraction and downstream consumability.

## 2026-07-03 C01 Package Skeleton

C01 now has a config-first package skeleton:

- `schemas/comsol_C01_matlab_server_bridge_runtime.schema.json`
- `configs/comsol/matlab_server_bridge_runtime/local_preflight.yaml`
- `configs/comsol/runtime_profiles/local_matlab_comsol_preflight.yaml`
- `src/science_capability_registry/comsol/matlab_server_bridge_runtime/`
- `tests/test_comsol_c01_schema.py`, `tests/test_comsol_c01_runner.py`, and `tests/test_comsol_c01_validation.py`

The implemented gate is `static-readiness` plus `preflight_only`: it validates environment boundary completeness and writes manifest/metrics/validation/report artifacts. It does not execute MATLAB on this host because the required runtime profile is not configured.
