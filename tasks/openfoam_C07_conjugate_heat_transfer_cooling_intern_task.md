# OpenFOAM C07 intern task: 共轭传热冷却

目标：在已完成的 OpenFOAM.com v2112 `chtMultiRegionSimpleFoam/multiRegionHeaterRadiation` packaged smoke baseline 上，继续把 C07 推进到可验证的 CHT integration capability。当前不能表述为已验证 benchmark；它只是 `smoke` gate 通过。

## 当前证据

- capability card: `software/openfoam/assets/C07_conjugate_heat_transfer_cooling.yaml`
- runtime profile: `configs/openfoam/runtime_profiles/openfoam_com_v2112_cht.yaml`
- default config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml`
- smoke report: `reports/openfoam_C07_conjugate_heat_transfer_cooling_multiRegionHeaterRadiation_baseline_smoke_2026-06-30.md`
- solver: `/opt/OpenFOAM-v2112/platforms/linux64GccDPInt32Opt/bin/chtMultiRegionSimpleFoam`
- tutorial: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/multiRegionHeaterRadiation`
- regions: fluid `bottomAir`, `topAir`; solid `heater`, `leftSolid`, `rightSolid`

`cpuCabinet` 保留为失败诊断 evidence：低并行数下 `realizableKE` 与 `kEpsilon` 都在 `Time=2` 附近 FPE，不再作为默认 packaged baseline。

## 必须交付

1. 建立至少三个 perturbation configs：heater fixed-temperature 升高、airflow/boundary 条件变化、mesh 或 decomposition sensitivity。
2. 为每个 perturbation 生成 runtime `metrics.json`、`validation.json`、`region_temperature_summary.csv`、`interface_balance_summary.csv` 和 human report。
3. 实现 patch-level heat-flux extraction 或等价守恒 proxy，替换当前 region-mean temperature difference proxy。
4. 增加 pytest：扰动趋势通过/失败测试、radiation artifact completeness 测试、heat-flux proxy 解析测试。
5. 更新 evidence index、capability catalog 和 asset card，只在 perturbation matrix 与 heat-flux proxy 通过后再考虑提升 `benchmark_status`。

## 验收门槛

- smoke：已完成。MHR baseline 在本机 WSL OpenFOAM.com v2112 到达 `Time=2`，五个 region 字段有限，radiation view-factor artifacts 和 validation artifacts 均生成。
- targeted-regression：baseline 加三类 perturbation 均通过，并记录清晰物理趋势。
- integration：baseline、perturbations、artifact contracts、registry default config、reports 和 evidence index 一致。
- double-v：后续再引入外部参考或更强守恒/热通量对比；在此之前不要把 C07 宣称为外部验证能力。

## 风险

- 当前 smoke 只有 `Time=2`，不代表稳态收敛。
- interface balance 仍是 region mean temperature proxy，不是 patch heat-flux conservation。
- 本机 OpenFOAM.com v2112/WSL functionObject 写出存在 `sha1` IO 风险；当前 baseline 通过清空 `controlDict.functions` 规避。
- `externalCoupledHeater` 带外部耦合接口，不能混入 C07 MHR perturbation matrix。
- `heatExchanger` 在 v2112 中没有 solid region，不能作为固-流 CHT 的主基准。
