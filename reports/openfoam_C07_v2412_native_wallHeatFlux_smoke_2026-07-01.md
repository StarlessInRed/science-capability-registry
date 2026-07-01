# OpenFOAM C07 v2412 native wallHeatFlux smoke - 2026-07-01

## 范围

本报告记录 C07 `conjugate_heat_transfer_cooling` 在 OpenFOAM.com v2412 上的 packaged `multiRegionHeaterRadiation` runtime smoke。目标是验证 v2412 是否能绕开 v2112 的 native `wallHeatFlux` sha1 IO blocker。

- config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2412.yaml`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2412/`
- runtime profile: `openfoam_com_v2412_cht`
- gate: `smoke`
- status: `passed`

## Runtime 结果

全部 runtime 命令返回 `0`：

- `./Allrun.pre`
- `checkMesh -allRegions -constant`
- `viewFactorsGen -region bottomAir`
- `viewFactorsGen -region topAir`
- `chtMultiRegionSimpleFoam`
- `chtMultiRegionSimpleFoam -postProcess -region bottomAir -func wallHeatFlux -latestTime`
- `chtMultiRegionSimpleFoam -postProcess -region topAir -func wallHeatFlux -latestTime`
- `chtMultiRegionSimpleFoam -postProcess -region heater -func wallHeatFlux -latestTime`
- `chtMultiRegionSimpleFoam -postProcess -region leftSolid -func wallHeatFlux -latestTime`
- `chtMultiRegionSimpleFoam -postProcess -region rightSolid -func wallHeatFlux -latestTime`

关键 metrics：

- final pseudo-time: `2.0`
- regions seen: `bottomAir`, `heater`, `leftSolid`, `rightSolid`, `topAir`
- max final residual: `0.08369735`
- validation checks: `67 / 67` passed
- max field-derived interface heat-rate mismatch: `0.9999435905632585` against smoke threshold `1.0`

Native `wallHeatFlux` fields were written and checked as expected outputs:

- `case/2/bottomAir/wallHeatFlux`
- `case/2/topAir/wallHeatFlux`
- `case/2/heater/wallHeatFlux`
- `case/2/leftSolid/wallHeatFlux`
- `case/2/rightSolid/wallHeatFlux`

## 版本差异

v2412 的官方 `Allrun` 对此 tutorial 不再调用 `faceAgglomerate`，而是直接运行 `viewFactorsGen`。本次配置按 v2412 官方路径收敛；generic `postProcess -func wallHeatFlux` 会因缺少 solver-created compressible turbulence model 失败，因此 native probe 使用 solver post-processing：`chtMultiRegionSimpleFoam -postProcess ...`。

## 状态结论

这条证据关闭了“native wallHeatFlux 在本机完全不可用”的版本级卡点：v2112 失败，v2412 可运行并写出字段。

但它仍不是 benchmark promotion 证据：

- horizon 仍是 `Time=2` short smoke
- native `wallHeatFlux` 字段存在不等于两侧 heat-rate parity 已经被验证
- steady convergence、regional energy balance、external/reference heat-flux target 仍未闭环
