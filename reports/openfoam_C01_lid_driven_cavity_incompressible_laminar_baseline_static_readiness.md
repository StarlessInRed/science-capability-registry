# OpenFOAM C01 baseline static-readiness report

## 范围

- capability: `C01_lid_driven_cavity_incompressible_laminar`
- gate: `static-readiness`
- case: `baseline`
- config: `configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline.yaml`
- schema: `schemas/openfoam_C01_lid_driven_cavity_incompressible_laminar.schema.json`
- package: `src/science_capability_registry/openfoam/lid_driven_cavity_incompressible_laminar/`

本报告记录 C01 早期 dry-run readiness。它只证明 schema、config、case generator 和 manifest 合同闭合，不代表真实 OpenFOAM solver 验证。

## 当前关系

该报告已被后续证据覆盖：

- `reports/openfoam_C01_lid_driven_cavity_incompressible_laminar_baseline_wsl_v2112_runtime_smoke.md`
- `reports/openfoam_C01_lid_driven_cavity_incompressible_laminar_benchmark_validation.md`
- `reports/openfoam_full_regression_2026-06-30.md`

因此，C01 当前状态以能力卡、benchmark validation report 和 full-regression summary 为准。

## 历史门禁结果

- dry-run case dictionary generation: passed
- manifest generation: passed
- required generated files listed: passed
- generated case files existed and were non-empty: passed
- `frontAndBack` mesh patch and `U/p` field boundary were `empty`: passed
- Reynolds number was positive and matched the baseline config: passed

## 当前状态

- `card_status`: `accepted`
- `benchmark_status`: `benchmark_validated`
- current evidence scope: local `openfoam_com_v2112` WSL integration matrix
- next gate: `double-v`

## 未完成风险

- C01 仍缺 Ghia 等外部中心线参考对比。
- Foundation/OpenFOAM-dev runtime compatibility has not been run.
- 当前证据不等同于 mesh/time independent external benchmark validation。
