# OpenFOAM C07 intern task: 共轭传热冷却

目标：把 OpenFOAM.com v2112 `chtMultiRegionSimpleFoam/cpuCabinet` 官方教程转成可复用、可配置、可验证的 CHT 冷却能力。当前只完成能力卡和 runtime profile 登记，不能把它表述为已验证 benchmark。

## 当前证据

- capability card: `software/openfoam/assets/C07_conjugate_heat_transfer_cooling.yaml`
- runtime profile: `configs/openfoam/runtime_profiles/openfoam_com_v2112_cht.yaml`
- solver: `/opt/OpenFOAM-v2112/platforms/linux64GccDPInt32Opt/bin/chtMultiRegionSimpleFoam`
- tutorial: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/cpuCabinet`
- regions: fluid `domain0`; solid `v_CPU`, `v_fins`

## 必须交付

1. 建立 `schemas/openfoam_C07_conjugate_heat_transfer_cooling.schema.json`，把 regionProperties、热物性、热源功率、环境温度、网格流程、并行分解、稳态迭代控制和验证阈值暴露为配置字段。
2. 建立 `configs/openfoam/conjugate_heat_transfer_cooling/baseline_cpu_cabinet_wsl_v2112.yaml`，只引用 `openfoam_com_v2112_cht`，不要复用单区域 profile。
3. 实现 dry-run case generator，复制官方 cpuCabinet 模板，并检查 `constant/regionProperties`、各 region 的 `0/` 字段、`constant/` 物性和 `system/` 字典完整。
4. 在 dry-run 稳定后再接入 runtime：`blockMesh`、`surfaceFeatureExtract`、`snappyHexMesh`、`decomposePar`、`splitMeshRegions`、`topoSet`、`chtMultiRegionSimpleFoam`、`reconstructParMesh`、`reconstructPar`。
5. 生成 `metrics.json`、`validation.json`、`region_temperature_summary.csv`、`interface_balance_summary.csv` 和 `validation_report.md`。
6. 增加 pytest：schema 拒绝测试、dry-run manifest 测试、runtime profile 测试、log parser 测试、metrics validation 测试和至少三个扰动趋势测试。

## 验收门槛

- static-readiness：能力卡、runtime profile、run schema、baseline config 和 dry-run manifest 全部通过测试。
- smoke：本机 WSL OpenFOAM.com v2112 跑通 baseline，所有 region 字段有限，日志无缺失 region solve。
- integration：至少包含 baseline、热源功率扰动、空气流动条件扰动、mesh/decomposition 扰动四类结果。
- double-v：后续再引入外部参考或更强守恒/热通量对比；在此之前不要把 C07 宣称为外部验证能力。

## 风险

- `cpuCabinet` 需要 snappyHexMesh、splitMeshRegions 和 parallel/reconstruct，比 C01/C03/C06 的 runner 复杂。
- `multiRegionHeaterRadiation` 带 radiation/viewFactors，`externalCoupledHeater` 带外部耦合接口，不能混入第一版 C07 baseline。
- `heatExchanger` 在 v2112 中没有 solid region，不能作为固-流 CHT 的主基准。
