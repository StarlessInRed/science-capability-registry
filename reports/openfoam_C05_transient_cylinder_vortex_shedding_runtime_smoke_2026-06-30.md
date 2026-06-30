# OpenFOAM C05 运行 smoke 证据 - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.transient_cylinder_vortex_shedding` 在本机 OpenFOAM.com v2112 / WSL 上的 runtime smoke 与 force extraction 诊断结果。

- solver-only config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_solver_smoke_wsl_v2112.yaml`
- native forceCoeffs config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_smoke_wsl_v2112.yaml`
- Python force proxy config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_wsl_v2112.yaml`
- solver-only result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_solver_smoke_wsl_v2112_20260630_002/`
- native forceCoeffs result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_smoke_wsl_v2112_20260630_002/`
- Python force proxy result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_wsl_v2112_20260630_002/`
- backend: WSL Ubuntu-24.04
- OpenFOAM profile: OpenFOAM.com v2112
- solver: `pimpleFoam`

## 结果

solver-only smoke 通过。

- `pimpleFoam` return code: 0
- final time: 1.0
- max Courant number: 0.3608741314689945
- max final residual: 0.005052265350342259
- force coefficient validation: disabled by config and marked not required
- validation status: passed

native forceCoeffs smoke 失败。

- `pimpleFoam` return code: 1
- failure class: OpenFOAM functionObject startup IO failure
- observed fatal: `FOAM FATAL IO ERROR ... IOstream "sha1"`
- force coefficient CSV: not produced
- Strouhal summary: not produced
- validation status: failed

Python patch-surface force proxy smoke 通过。

- `pimpleFoam` return code: 0
- final time: 1.0
- max Courant number: 0.3608741314689945
- max final residual: 0.005052265350342259
- force extraction source: `python_patch_surface_proxy`
- force coefficient rows: 4
- output: `postprocess/force_coefficients.csv`
- validation status: passed
- Strouhal estimate: disabled for this short smoke

## 实现修正

- Run schema 新增 `postprocess.force_extraction_source`，可显式选择 `openfoam_forceCoeffs` 或 `python_patch_surface_proxy`。
- native `forceCoeffs` 仍保留为首选路径，但在本机 v2112/WSL 上被 `sha1` IO 行为阻断。
- Python proxy 从保留的 `constant/polyMesh`、时间步 `p/U` 场和配置中的 wall patch 计算短时 lift/drag proxy，并写出统一 CSV。
- validation 现在要求 runtime summary 中的 `force_coefficients_source` 必须匹配配置来源，避免把 native 与 proxy 结果混用。
- Strouhal validation 只有在 `postprocess.strouhal_estimate: true` 且 summary 明确 `available: true` 时才允许通过。

## 判定

C05 已关闭“force artifact 完全无法生成”的短时 smoke 卡点，但只是在 Python patch-surface proxy 层面闭环。native OpenFOAM `forceCoeffs` parity、长时域升阻力时序、Strouhal 估计和网格/时间步敏感性仍未闭环。

`benchmark_status` 必须保持 `package_skeleton_created`。当前证据可以证明官方 `cylinder2D` case 可完成短时域 solver smoke，并能用配置显式的 Python proxy 生成 force coefficient CSV；不能证明涡街频率、Strouhal 或 benchmark 级力系数精度。
