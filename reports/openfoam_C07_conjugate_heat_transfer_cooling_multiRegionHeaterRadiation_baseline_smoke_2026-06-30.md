# OpenFOAM C07 multiRegionHeaterRadiation packaged smoke - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.conjugate_heat_transfer_cooling` 的第一版可执行 packaged baseline：

- config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml`
- tutorial source: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/multiRegionHeaterRadiation`
- runtime profile: `configs/openfoam/runtime_profiles/openfoam_com_v2112_cht.yaml`
- result root: `_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112_20260630_002/`
- gate: `smoke`

该 gate 只证明本机 OpenFOAM.com v2112 能通过配置化 runner 复制官方模板、执行多区域 CHT radiation 预处理、运行 `chtMultiRegionSimpleFoam` 到短时终点，并生成机器可读 metrics/validation/postprocess artifacts。它不声明稳态收敛、热通量守恒或 benchmark-grade validation。

## 配置化基线

- fluid regions: `bottomAir`, `topAir`
- solid regions: `heater`, `leftSolid`, `rightSolid`
- thermal driver: `heater:minY` 固定温度边界 `500 K`
- control: `endTime=2`, `deltaT=1`, `writeInterval=1`, `writeFormat=ascii`
- disabled functionObjects: 清空 `system/controlDict` 的 `functions` block，避免本机 v2112/WSL functionObject 写出触发已知 `sha1` IO failure

命令序列：

1. `./Allrun.pre`
2. `checkMesh -allRegions -constant`
3. `faceAgglomerate -region bottomAir`
4. `viewFactorsGen -region bottomAir`
5. `faceAgglomerate -region topAir`
6. `viewFactorsGen -region topAir`
7. `chtMultiRegionSimpleFoam`

## 结果

所有命令 return code 均为 0。`checkMesh` 覆盖五个 region，`mesh_ok=true`，cell counts 为 `bottomAir 1460`, `topAir 1200`, `heater 80`, `leftSolid 130`, `rightSolid 130`。

Solver 到达 `Time = 2`，五个 region 均被解析到，无 `FOAM FATAL` 或真实 floating-point exception。短时 smoke 最大 final residual 为 `0.08369737`，低于本 smoke 配置阈值 `0.1`。该阈值只用于短时非发散检查，不代表稳态收敛。

温度摘要：

| region | min T K | max T K | mean T K |
| --- | ---: | ---: | ---: |
| bottomAir | 300.0041 | 311.7886 | 300.1462 |
| topAir | 300.0000 | 300.0022 | 300.0003 |
| heater | 300.0001 | 418.5100 | 316.6354 |
| leftSolid | 300.0000 | 300.0335 | 300.0009 |
| rightSolid | 300.0000 | 300.0622 | 300.0017 |

Interface proxy 使用 region mean temperature difference，不是 patch heat-flux conservation：

| interface | mean abs delta T K |
| --- | ---: |
| bottomAir_to_heater | 16.4892 |
| topAir_to_heater | 16.6351 |
| heater_to_leftSolid | 16.6345 |
| heater_to_rightSolid | 16.6337 |

## 判定

`validation.json` 结果为 `passed=true`，`gate=smoke`，`benchmark_status=runtime_smoke_verified`。这可以关闭 C07 当前“无可执行 baseline”的能力卡卡点，并将 packaged baseline 从 `cpuCabinet` 切换到 `multiRegionHeaterRadiation`。

仓库级 `benchmark_status` 仍应保持 `benchmark_candidate`。原因：

- 当前运行只有 `Time = 2`，不是稳态收敛验证。
- interface balance 仍是 region-mean temperature proxy，不是 patch-level heat-flux mismatch。
- 尚无至少三组扰动矩阵：heater temperature/power、airflow/boundary condition、mesh/decomposition sensitivity。
- `cpuCabinet` 仍保留为已诊断失败的官方 tutorial evidence，不再作为默认 packaged baseline。

## 后续验证任务

1. 增加 heater fixed-temperature perturbation，验证 heater/bottomAir 最高温度随热驱动增强而上升。
2. 增加 airflow 或 topAir inlet perturbation，验证流体冷却响应方向。
3. 增加 mesh/decomposition sensitivity，确认短时 smoke 不依赖单一网格/分区。
4. 实现 patch-level heat-flux extraction，再把 interface proxy 从 region mean temperature 差升级为热通量守恒检查。
