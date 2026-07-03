# COMSOL Examples Index

本文件登记 COMSOL / LiveLink for MATLAB 首批能力资产使用的来源类型。当前没有提交本机 `.mph`、MATLAB 脚本或 COMSOL runtime 输出；所有 runtime evidence 后续必须进入 `_results/comsol/`。

## Source Packages

| source_id | source | role | current status |
| --- | --- | --- | --- |
| `comsol_livelink_for_matlab_product` | `https://www.comsol.com/livelink-for-matlab` | Product capability evidence for MATLAB-driven COMSOL modeling and result extraction. | indexed source |
| `comsol_livelink_for_matlab_users_guide` | `https://doc.comsol.com/6.3/doc/com.comsol.help.llmatlab/LiveLinkForMATLABUsersGuide.pdf` | API and command-line reference candidate. | indexed source |
| `comsol_application_libraries` | local COMSOL Application Libraries, path to be configured by environment | Official example/model source candidate. | C03-C06 candidate set selected; execution still env-rooted |
| `self_generated_matlab_driver_scripts` | repo configs/scripts generated from capability contracts | First reproducible runtime route. | package-backed C01-C06 |

## Seed Mapping

| C | asset path | source candidates | first runtime action | current gate |
| --- | --- | --- | --- | --- |
| C01 | `software/comsol/assets/C01_matlab_server_bridge_runtime.yaml` | LiveLink API, self-generated minimal model | MATLAB starts or connects to COMSOL and extracts one finite scalar | runtime smoke passed |
| C02 | `software/comsol/assets/C02_model_construction_api_contract.yaml` | LiveLink model tree/API commands | build model tree, parameters, material, geometry, mesh, study | runtime smoke passed |
| C03 | `software/comsol/assets/C03_geometry_mesh_import_contract.yaml` | generated geometry, later official Application Library model | emit geometry/mesh/selection manifest | runtime smoke passed |
| C04 | `software/comsol/assets/C04_physics_boundary_assignment_contract.yaml` | C02/C03 generated model | assign physics, materials, BC/IC and validate completeness | runtime smoke passed |
| C05 | `software/comsol/assets/C05_study_run_solver_smoke.yaml` | C04 complete model | run study, check solver status, keep result dataset | runtime smoke passed |
| C06 | `software/comsol/assets/C06_result_extraction_postprocess_validation.yaml` | solved C05 model | export canonical probes/tables/units for downstream use | runtime smoke passed |

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

The current C01 runner separates `dry_run_only`, `preflight_only`, and `matlab_livelink_smoke`. The committed smoke config is `configs/comsol/matlab_server_bridge_runtime/local_livelink_smoke.yaml`, and stable evidence is recorded in `reports/comsol_C01_matlab_server_bridge_runtime_livelink_smoke_2026-07-03.md`.

## 2026-07-03 C02-C06 Package Boundary

- C02 package config: `configs/comsol/model_construction_api_contract/local_livelink_model_tree_smoke.yaml`
- C03 package config: `configs/comsol/geometry_mesh_import_contract/local_livelink_heat_rectangle.yaml`
- C04 package config: `configs/comsol/physics_boundary_assignment_contract/local_livelink_heat_rectangle.yaml`
- C05 package config: `configs/comsol/study_run_solver_smoke/local_livelink_heat_rectangle.yaml`
- C06 package config: `configs/comsol/result_extraction_postprocess_validation/local_livelink_heat_rectangle.yaml`

C02 has local LiveLink model-tree smoke evidence. C03-C06 now have generated heat-rectangle LiveLink runtime smoke evidence. Do not interpret these generated-case artifacts as official `.mph` replay, double-v, analytical benchmark validation, or broad multiphysics correctness.

## 2026-07-03 C03-C06 Official Replay Candidate Set

Candidate config:

- `configs/comsol/application_library_replay_candidates/c03_c06_official_candidates.yaml`

Primary candidates:

- `LiveLink_for_MATLAB/Tutorials/domain_activation_llmatlab.m` plus `.mph`
- `LiveLink_for_MATLAB/Tutorials/pseudoperiodicity_llmatlab.m` plus `.mph`

Secondary Heat Transfer candidates:

- `Heat_Transfer_Module/Verification_Examples/thin_plate.mph`
- `Heat_Transfer_Module/Tutorials,_Conduction/cylinder_conduction.mph`
- `Heat_Transfer_Module/Verification_Examples/localized_heat_source.mph`
- `Heat_Transfer_Module/Verification_Examples/semi_infinite_wall.mph`

All paths are relative to `COMSOL_APPLICATION_LIBRARY_ROOT`. This index records candidate selection only; it does not claim official replay execution.

## 2026-07-03 Official Replay Contract

Shared replay configs:

- `configs/comsol/application_library_replay/domain_activation_official_replay_smoke.yaml`
- `configs/comsol/application_library_replay/pseudoperiodicity_official_replay_export_smoke.yaml`

The first config targets the `domain_activation_llmatlab` official tutorial as the C03-C06 replay smoke. The second targets `pseudoperiodicity_llmatlab` as the richer C06 export/table replay candidate. Both remain env-rooted through `COMSOL_APPLICATION_LIBRARY_ROOT`.

Runtime smoke reports:

- `reports/comsol_C03_C06_domain_activation_official_replay_smoke_2026-07-03.md`
- `reports/comsol_C06_pseudoperiodicity_official_replay_export_smoke_2026-07-03.md`

These reports prove official replay smoke only. They are not full tutorial parity or benchmark validation.
