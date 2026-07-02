# Fluent examples_index

本文登记 Fluent 官方教程、Workbench 教程、verification manual 和 legacy 素材在能力资产中的角色。根目录 PDF 和 case package 不强行一一对应；verification manual 当前作为 reference source，而不是已发现的可运行 package。

## Source Packages

| source_id | logical path | source_role | observed contents | capability use |
| --- | --- | --- | --- | --- |
| fluent_tutorial_guide_2025_r1_pdf | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Ansys_Fluent_Tutorial_Guide_2025_R1.pdf` | tutorial guide | Fluent 官方 tutorial 文档 | 解释 setup workflow、模型选项、postprocess 操作 |
| fluent_tutorial_package_2025_r1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Tutorial_Package` | tutorial case package | 75 个 zip | C01/C03/C04/C05/C06/C07 runtime/replay 候选 |
| fluent_workbench_tutorial_2025_r1_pdf | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Ansys_Fluent_Workbench_Tutorial_Guide_2025_R1.pdf` | Workbench guide | Workbench tutorial 文档 | C08 problem-definition 和参数化链路 |
| fluent_workbench_tutorial_package_2025_r1 | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_Workbench_Tutorial_Package` | Workbench package | `workbench_elbow.zip`、`workbench_matpro_blowmold.zip`、`workbench_parameter.zip` | C08 integration seed |
| fluid_dynamics_verification_manual | `AgentKnowledge/case_library/fluent/cases/official_tutorials/ansys_fluid_dynamics_verification_manual.pdf` | verification/reference | 未发现同名 case package | C02 reference policy 和 benchmark promotion |
| fluent_legacy_tutorial_case | `AgentKnowledge/case_library/fluent/cases/official_tutorials/Fluent_tutorial_case` | legacy tutorial case | `UserGuide_17.06.pdf`、`ch03`-`ch16`、直接 `.cas/.dat/.msh/.jou/.wbpj` | 早期 standalone runtime seed |
| fluent_legacy_2020_r2_unique | `AgentKnowledge/case_library/fluent/cases/official_tutorials/legacy_2020_r2_unique` | legacy supplement | `single_rotating.zip` | C06 rotating/sliding supplement |

## Seed Mapping

| C | asset path | primary candidates | replay role | next gate |
| --- | --- | --- | --- | --- |
| C01 | `software/fluent/assets/C01_steady_internal_flow_runtime.yaml` | legacy `ch07/elbow`, `ch07/nozzle`; tutorial `introduction.zip` if DSCO workflow is supported | compare self-generated journal with direct legacy case replay | runtime smoke passed; pressure-drop parser pending |
| C02 | `software/fluent/assets/C02_verification_reference_validation.yaml` | verification manual VMFL005 Poiseuille pipe | compare self-generated case against Hagen-Poiseuille pressure-drop target | static reference package created; self-generated runtime pending |
| C03 | `software/fluent/assets/C03_mesh_convergence_trend.yaml` | `fluent_adaptation.zip`, C01 perturbation | compare residual/field trend across mesh or adaptation changes | targeted-regression |
| C04 | `software/fluent/assets/C04_external_aero_force_coefficients.yaml` | `fluent_aero_tutorial.zip`, `sedan_2m.zip` | compare Cd/Cl/Cp and reference CSV where available | force/Cp smoke |
| C05 | `software/fluent/assets/C05_vof_free_surface_transient.yaml` | `vof.zip`, legacy `ch10/dambreak`, tank flush cases | compare interface and volume-fraction evolution | transient VOF smoke |
| C06 | `software/fluent/assets/C06_sliding_rotating_mesh.yaml` | `sliding_mesh.zip`, `single_rotating.zip` | compare rotating/sliding-zone setup and time history | moving mesh smoke |
| C07 | `software/fluent/assets/C07_heat_transfer_energy_balance.yaml` | `2d_heat_exchanger_optimizer.zip`, `effusion_cooling.zip`, battery thermal cases | compare temperature range and energy balance | heat-transfer smoke |
| C08 | `software/fluent/assets/C08_workbench_parameter_integration.yaml` | `workbench_parameter.zip`, `workbench_elbow.zip` | compare Workbench parameter and result handoff | Workbench preflight |

## Static Contract

| contract | path | role | status |
| --- | --- | --- | --- |
| Fluent C01-C08 seed suite | `configs/fluent/seed_suite/c01_c08_static_readiness.yaml` | Holds the first 8 seed cases, required source roles, self-generated/replay/comparison modes, and static validation targets. | `static-readiness` |
| Fluent seed suite schema | `schemas/fluent_seed_suite.schema.json` | Rejects missing/unknown fields and requires exactly C01-C08 benchmark-candidate seeds. | active |
| Fluent seed suite dry-run package | `src/science_capability_registry/fluent/seed_suite/` | Generates `seed_suite_manifest.json`, `seed_cases.json`, `metrics.json`, `validation.json`, and `validation_report.md` without launching Fluent. | active |
| Fluent C01 runtime package | `src/science_capability_registry/fluent/steady_internal_flow_runtime/` | Runs the legacy elbow case in Fluent batch mode, parses residuals and mass-flow balance, and writes smoke evidence. | `runtime_smoke_passed` |
| Fluent C02 reference package | `src/science_capability_registry/fluent/verification_reference_validation/` | Converts VMFL005 pressure-drop reference into schema/config/manifest/metrics/report. | `static-readiness` |
| Fluent official replay manifest | `src/science_capability_registry/fluent/official_replay_manifest/` | Classifies C01-C08 official zip, legacy, Workbench, and verification sources without extraction or solver execution. | `static-readiness` |

## Intake Rules

- Official tutorial zip is capability evidence, not benchmark truth.
- Verification manual is the first source for benchmark targets, but requires geometry/reference homology before promotion.
- Workbench tutorials define problem organization and parameter workflows; they must not be mixed with standalone Fluent batch gates.
- Legacy direct `.cas/.dat/.jou` cases are acceptable early runtime seeds when clearly labeled as legacy source.
