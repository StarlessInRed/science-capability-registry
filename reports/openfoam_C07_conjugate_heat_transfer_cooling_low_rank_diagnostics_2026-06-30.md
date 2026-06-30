# OpenFOAM C07 低并行数诊断证据 - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.conjugate_heat_transfer_cooling` 的官方 `cpuCabinet` 低并行数诊断，用于判断当前 blocker 是否来自过高并行分解或仍是 tutorial/solver 路径中的物理数值失败。

- tutorial source: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/cpuCabinet`
- OpenFOAM profile: OpenFOAM.com v2112
- backend: WSL Ubuntu-24.04
- solver: `chtMultiRegionSimpleFoam`
- primary result root: `_results/openfoam/conjugate_heat_transfer_cooling/cpuCabinet_np2_realizableKE_diag_20260630_004/`
- primary script: `_results/openfoam/conjugate_heat_transfer_cooling/run_c07_np2_realizableKE_diag_20260630_004.sh`

## 诊断矩阵

`np=1` 不能作为有效 solver 对照：官方 `Allrun.pre` 中的并行 utility 在 `-parallel` 模式下拒绝单进程运行，报错为 `attempt to run parallel on 1 processor`。因此本轮最小可执行低并行数诊断为 `np=2`。

`np=2` 诊断配置：

- `system/**/decomposeParDict`: `numberOfSubdomains 2`, `n (2 1 1)`
- `system/controlDict`: `endTime 5`, `writeInterval 1`, `functions {}`
- turbulence model: official `realizableKE`
- command sequence: `./Allrun.pre`, `checkMesh -allRegions -constant -parallel`, `chtMultiRegionSimpleFoam -parallel`

## 结果

- `./Allrun.pre` return code: 0
- `checkMesh -allRegions -constant -parallel` return code: 0
- solver return code: 136
- solver failure time: `Time = 2`
- failure stack: `compressibleTurbulenceModel::phi()` -> `RASModels::realizableKE::correct()`
- observed field symptom: continuity error jumps to `sum local = 11512.223`, density range becomes `0 21923.217`
- validation status: failed diagnostic evidence

该结果与此前 probe-mitigation 后的官方 case debug 一致：移除 functionObject/probes 和降低并行数后，仍会在 `realizableKE::correct()` 进入 floating-point exception。

## 判定

C07 的当前 blocker 不应归因于 MPI slots、OpenFOAM functionObject `sha1` IO 或高并行数本身。低并行数下 mesh pipeline 可以完成，mesh check 也通过，但 solver 仍在 Time=2 出现 realizableKE/FPE。

`benchmark_status` 必须保持 `benchmark_candidate`。下一步应做 closure-level 对照：至少比较 `realizableKE` 与 `kEpsilon`，并评估是否转向 OpenFOAM.com v2112 的其他 CHT tutorial，例如 `multiRegionHeaterRadiation` 或 `externalCoupledHeater`，以避免把一个不可稳定运行的官方 tutorial 固化成 MatOS 能力基线。
