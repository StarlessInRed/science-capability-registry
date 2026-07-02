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
| C01 | `matlab_server_bridge_runtime` | MATLAB-COMSOL server/session bridge and minimal roundtrip | LiveLink API and self-generated minimal model | executable profile, server/session connection, model open/create, finite scalar extraction | runtime smoke passed |
| C02 | `model_construction_api_contract` | Build a COMSOL model from MATLAB-controlled API calls | generated heat/PDE model contract | model tree tags, parameters, material, geometry, mesh, study object creation | runtime smoke passed |
| C03 | `geometry_mesh_import_contract` | Geometry, mesh, import, and selection-map readiness | generated geometry first, official model later | entity counts, selections, boundary role map, mesh/import status | package skeleton static-readiness |
| C04 | `physics_boundary_assignment_contract` | Physics interface, material, boundary, and initial-condition assignment | C02/C03 generated model or official small model | BC/IC completeness, units, physics feature tags, rejection of missing assignments | package skeleton static-readiness |
| C05 | `study_run_solver_smoke` | Study execution, solver status, and benchmark-ready result state | C04 complete model | solver completion, convergence/status, final datasets, nonempty result state | package skeleton static-readiness before smoke |
| C06 | `result_extraction_postprocess_validation` | MATLAB-side extraction, canonical exports, and downstream consumability | solved C05 result | `mphglobal`/`mphinterp`/tables, units, finite values, CSV/JSON handoff | package skeleton static-readiness |

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

C01 已通过本机 MATLAB LiveLink smoke：MATLAB batch 连接本地 COMSOL server，创建最小 model，并通过 `mphevaluate` 抽取有限标量。C02-C06 仍停留在 static-readiness，不声明 C02 benchmark validation 或 COMSOL solver execution。

后续进入 runtime 前必须配置：

- `MATLAB_EXE`: MATLAB executable path.
- `COMSOL_EXE` or `COMSOL_BIN`: COMSOL command/client path.
- `COMSOL_MPHSERVER_BIN`: COMSOL server path when server mode is used.
- `COMSOL_MLI_DIR`: LiveLink for MATLAB API path if not auto-discoverable.
- `COMSOL_APPLICATION_LIBRARY_ROOT`: optional official model library root.

## Next Gates

1. C02 model construction API contract.
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

## 2026-07-03 C01 LiveLink Smoke

C01 runtime smoke is now passed through `configs/comsol/matlab_server_bridge_runtime/local_livelink_smoke.yaml`.

Evidence:

- `reports/comsol_C01_matlab_server_bridge_runtime_livelink_smoke_2026-07-03.md`
- `_results/comsol/matlab_server_bridge_runtime/local_livelink_smoke/`

The smoke proves bridge connectivity and finite COMSOL parameter evaluation only. It does not prove study solve, field extraction, official model replay, or physics benchmark validation.

## 2026-07-03 C02-C06 Package Closure

C02 now has a package-backed MATLAB LiveLink model-tree smoke:

- `schemas/comsol_C02_model_construction_api_contract.schema.json`
- `configs/comsol/model_construction_api_contract/local_livelink_model_tree_smoke.yaml`
- `src/science_capability_registry/comsol/model_construction_api_contract/`
- `reports/comsol_C02_model_construction_api_contract_livelink_smoke_2026-07-03.md`
- `_results/comsol/model_construction_api_contract/local_livelink_model_tree_smoke/`

The C02 smoke passed with `matlab_return_code=0`, `finite_parameter_count=3/3`, `required_tag_missing_count=0`, and `solver_executed=false`.

C03-C06 now have package-backed static contracts:

- C03: `configs/comsol/geometry_mesh_import_contract/static_contract.yaml`
- C04: `configs/comsol/physics_boundary_assignment_contract/static_contract.yaml`
- C05: `configs/comsol/study_run_solver_smoke/static_contract.yaml`
- C06: `configs/comsol/result_extraction_postprocess_validation/static_contract.yaml`

These C03-C06 packages emit manifest, metrics, validation, report, and stage-specific handoff artifacts. They do not execute COMSOL runtime, open official models, run solvers, extract finite fields, or claim benchmark validation.
