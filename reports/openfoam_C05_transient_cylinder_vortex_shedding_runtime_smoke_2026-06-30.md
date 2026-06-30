# OpenFOAM C05 运行 smoke 证据 - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.transient_cylinder_vortex_shedding` 在本机 OpenFOAM.com v2112 / WSL 上的 runtime smoke 结果。

- solver-only config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_solver_smoke_wsl_v2112.yaml`
- force-enabled config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_smoke_wsl_v2112.yaml`
- solver-only result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_solver_smoke_wsl_v2112_20260630_002/`
- force-enabled result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_smoke_wsl_v2112_20260630_002/`
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

force-enabled smoke 失败。

- `pimpleFoam` return code: 1
- failure class: OpenFOAM functionObject startup IO failure
- observed fatal: `FOAM FATAL IO ERROR ... IOstream "sha1"`
- force coefficient CSV: not produced
- Strouhal summary: not produced
- validation status: failed

## 代码修正

- `Allrun.pre` 会调用 `restore0Dir`，因此 runtime patch 必须同时修改 `0/U` 与 `0.orig/U`。本次已修正，否则入口速度会被官方模板覆盖。
- command log 文件名改为包含命令序号与完整命令，避免多个 `mpirun` 步骤覆盖同一个 `log.mpirun`。
- runtime parser 现在把 `sigFpe::sigHandler` stack 识别为 fatal。
- postprocess 现在会在 `case/postProcessing` 与 `case/processor*/postProcessing` 下查找 `coefficient.dat`。
- solver-only smoke 允许通过配置关闭 forceCoeffs，并在 validation 中显式记录 `postprocess.force_coefficients_not_required`。

## 判定

C05 目前关闭了“完全没有 pimpleFoam runtime metrics”的卡点，但没有关闭力系数和 Strouhal 卡点。

`benchmark_status` 必须保持 `package_skeleton_created`。当前证据只能证明官方 cylinder2D case 在 forceCoeffs 关闭时可完成短时域 solver smoke；不能证明涡街频率、升阻力时序、Strouhal 或网格/时间步敏感性。

下一步应优先解决 v2112/WSL functionObject `sha1` IO 问题，或实现不依赖 OpenFOAM functionObject 的 Python force extraction，再补长时域和敏感性矩阵。
