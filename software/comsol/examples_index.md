# COMSOL Examples Index

本文件登记 COMSOL / LiveLink for MATLAB 首批能力资产使用的来源类型。当前没有提交本机 `.mph`、MATLAB 脚本或 COMSOL runtime 输出；所有 runtime evidence 后续必须进入 `_results/comsol/`。

## Source Packages

| source_id | source | role | current status |
| --- | --- | --- | --- |
| `comsol_livelink_for_matlab_product` | `https://www.comsol.com/livelink-for-matlab` | Product capability evidence for MATLAB-driven COMSOL modeling and result extraction. | indexed source |
| `comsol_livelink_for_matlab_users_guide` | `https://doc.comsol.com/6.3/doc/com.comsol.help.llmatlab/LiveLinkForMATLABUsersGuide.pdf` | API and command-line reference candidate. | indexed source |
| `comsol_application_libraries` | local COMSOL Application Libraries, path to be configured by environment | Official example/model source candidate. | not configured on this host |
| `self_generated_matlab_driver_scripts` | future repo configs/scripts generated from capability contracts | First reproducible runtime route. | planned |

## Seed Mapping

| C | asset path | source candidates | first runtime action | current gate |
| --- | --- | --- | --- | --- |
| C01 | `software/comsol/assets/C01_matlab_server_bridge_runtime.yaml` | LiveLink API, self-generated minimal model | MATLAB starts or connects to COMSOL and extracts one finite scalar | package skeleton + preflight runner; runtime smoke pending |
| C02 | `software/comsol/assets/C02_model_construction_api_contract.yaml` | LiveLink model tree/API commands | build model tree, parameters, material, geometry, mesh, study | static-readiness |
| C03 | `software/comsol/assets/C03_geometry_mesh_import_contract.yaml` | generated geometry, later official Application Library model | emit geometry/mesh/selection manifest | static-readiness |
| C04 | `software/comsol/assets/C04_physics_boundary_assignment_contract.yaml` | C02/C03 generated model | assign physics, materials, BC/IC and validate completeness | static-readiness |
| C05 | `software/comsol/assets/C05_study_run_solver_smoke.yaml` | C04 complete model | run study, check solver status, keep result dataset | static-readiness |
| C06 | `software/comsol/assets/C06_result_extraction_postprocess_validation.yaml` | solved C05 model | export canonical probes/tables/units for downstream use | static-readiness |

## Runtime Prohibition

- Do not claim COMSOL runtime without a recorded MATLAB/COMSOL executable profile.
- Do not treat a `.mph` file opening as benchmark validation.
- Do not store local executable paths, license paths, or server secrets in committed configs.
- Do not commit large `.mph` or generated result files unless an explicit small fixture policy is created.

## 2026-07-03 C01 Runtime Boundary

C01 package skeleton paths:

- `configs/comsol/matlab_server_bridge_runtime/local_preflight.yaml`
- `schemas/comsol_C01_matlab_server_bridge_runtime.schema.json`
- `src/science_capability_registry/comsol/matlab_server_bridge_runtime/`

The current C01 runner separates `dry_run_only`, `preflight_only`, and `matlab_livelink_smoke`. The committed config stays on `preflight_only`; `matlab_livelink_smoke` requires local environment variables and a stable runtime evidence summary before it can be claimed.
