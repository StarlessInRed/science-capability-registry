# OpenFOAM C07 closure 与替代 tutorial 诊断证据 - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.conjugate_heat_transfer_cooling` 的两个后续诊断：

- `cpuCabinet` 在 `np=2` 下从 `realizableKE` 切换到 `kEpsilon` 的 closure 对照。
- `multiRegionHeaterRadiation` 官方 tutorial 的短时 OpenFOAM.com v2112 运行探针。

两个诊断都只用于定位 C07 当前卡点，不提升 `benchmark_status`。

## cpuCabinet kEpsilon 对照

- tutorial source: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/cpuCabinet`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/cpuCabinet_np2_kEpsilon_diag_20260630_001/`
- script: `_results/openfoam/conjugate_heat_transfer_cooling/run_c07_np2_kEpsilon_diag_20260630_001.sh`
- decomposition: `np=2`
- turbulence model: `kEpsilon`

结果：

- `./Allrun.pre` return code: 0
- `checkMesh -allRegions -constant -parallel` return code: 0
- `chtMultiRegionSimpleFoam -parallel` return code: 136
- solver failure time: `Time = 2`
- failure stack: `compressibleTurbulenceModel::phi()` -> `RASModels::kEpsilon::correct()`
- observed field symptom: density range becomes `0 7463.6886`, continuity local error reaches `52159.859`

该结果说明 C07 的 `cpuCabinet` blocker 不只属于 `realizableKE`。在 `kEpsilon` 下仍会进入相同的 turbulence/phi 路径并 FPE。

## multiRegionHeaterRadiation 短时探针

- tutorial source: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/multiRegionHeaterRadiation`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/multiRegionHeaterRadiation_short_wsl_v2112_20260630_001/`
- script: `_results/openfoam/conjugate_heat_transfer_cooling/run_c07_alt_multiRegionHeaterRadiation_short_20260630_001.sh`
- fluid regions: `bottomAir`, `topAir`
- solid regions: `heater`, `leftSolid`, `rightSolid`

结果：

- `./Allrun.pre` return code: 0
- `checkMesh -allRegions` return code: 0
- `faceAgglomerate` for `bottomAir` and `topAir`: return code 0
- `viewFactorsGen` for `bottomAir` and `topAir`: return code 0
- `chtMultiRegionSimpleFoam` return code: 0
- solver reached `Time = 2` and `End`
- temperature maxima at `Time = 2`: `bottomAir 380.5091`, `topAir 300.0399`, `heater 500`, `leftSolid 300.0546`, `rightSolid 300.1017`

该结果证明本机 OpenFOAM.com v2112 可以运行至少一个多区域 CHT tutorial 到短时终点。它只是替代候选 smoke，不是热通量守恒或扰动矩阵验证。

## 判定

`cpuCabinet` 当前不适合作为立刻固化的 C07 baseline：`realizableKE` 与 `kEpsilon` 都在 `Time = 2` 失败。下一步应把 C07 的可执行 baseline 候选切换到 `multiRegionHeaterRadiation`，并为其建立 config-first run schema、短时 runtime validation、温度趋势和界面热通量 proxy。

`benchmark_status` 必须保持 `benchmark_candidate`。
