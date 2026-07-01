# OpenFOAM C07 native wallHeatFlux diagnostic - 2026-07-01

## 范围

本报告记录 C07 `multiRegionHeaterRadiation` packaged runtime case 上的 native heat-flux 后处理尝试。

- capability: `C07_conjugate_heat_transfer_cooling`
- baseline config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112`
- case: `case/`
- OpenFOAM profile: `openfoam_com_v2112_cht`
- attempted function: `postProcess -region <region> -func wallHeatFlux -latestTime`
- tested regions: `bottomAir`, `topAir`, `heater`, `leftSolid`, `rightSolid`

## 执行结果

OpenCFD v2112 的 `postProcess` 不支持 `-allRegions`，因此按 legacy CHT multi-region layout 逐 region 执行：

| region | command | return code | log |
| --- | --- | ---: | --- |
| bottomAir | `postProcess -region bottomAir -func wallHeatFlux -latestTime` | 1 | `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112/logs/log.native_wallHeatFlux_bottomAir` |
| topAir | `postProcess -region topAir -func wallHeatFlux -latestTime` | 1 | `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112/logs/log.native_wallHeatFlux_topAir` |
| heater | `postProcess -region heater -func wallHeatFlux -latestTime` | 1 | `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112/logs/log.native_wallHeatFlux_heater` |
| leftSolid | `postProcess -region leftSolid -func wallHeatFlux -latestTime` | 1 | `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112/logs/log.native_wallHeatFlux_leftSolid` |
| rightSolid | `postProcess -region rightSolid -func wallHeatFlux -latestTime` | 1 | `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112/logs/log.native_wallHeatFlux_rightSolid` |

每个 region 均在创建 region mesh 后触发相同错误：

```text
FOAM FATAL IO ERROR: (openfoam-2112)
error in IOstream "sha1" for operation Foam::Ostream& Foam::operator<<(Ostream&, const word&)
file: sha1 at line 0.
```

## 判定

本机 OpenFOAM.com v2112 / WSL 上，C07 native `wallHeatFlux` 后处理当前不可用；失败模式与前序 functionObject `sha1` IO blocker 一致。

因此 C07 的当前可执行状态保持为：

- `multiRegionHeaterRadiation` baseline and perturbation matrix: runtime smoke/integration passed。
- heat-flux evidence: Python paired-patch owner-cell proxy only。
- native heat-flux closure: failed diagnostic evidence。
- benchmark promotion: 不允许，保持 `benchmark_candidate`。

## 下一步判据

C07 后续只有在以下任一条件满足时，才可考虑把 heat-flux gate 从 proxy 提升到 native/reference：

1. 在另一个 OpenFOAM.com 版本或另一台机器上，`postProcess -region <region> -func wallHeatFlux -latestTime` 能对所有 region 成功产出 native wallHeatFlux 场。
2. 引入独立 reference 或 face-field integration parity，并明确标注为非 native OpenFOAM functionObject。
3. 同时补齐更长稳态收敛证据和区域能量平衡，不只依赖 Time=2 smoke。
