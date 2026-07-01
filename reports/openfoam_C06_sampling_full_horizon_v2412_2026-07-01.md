# OpenFOAM C06 v2412 sampling and full-horizon evidence - 2026-07-01

## 范围

本报告记录 C06 `dam_break_vof_free_surface` 在 OpenFOAM.com v2412 / WSL profile 下补齐的两个局部卡点：

- native `sampleSets` 产物存在性检查
- `endTime = 1.0 s` full-horizon runtime 检查

它不是外部实验或独立参考 double-v 证据。

## Sampling parity runtime

- config: `configs/openfoam/dam_break_vof_free_surface/sampling_parity_wsl_v2412.yaml`
- result root: `_results/openfoam/dam_break_vof_free_surface/sampling_parity_wsl_v2412/`
- gate: `targeted-regression`
- status: `passed`
- final time: `0.1`
- max Courant: `0.95975`
- max alpha Courant: `0.822277`
- native sample root: `case/postProcessing/sampleSets`
- sample files: `58`
- numeric time directories: `29`
- latest sample time: `0.1`
- gauges: `gauge_1`, `gauge_2`
- file type: `.vtp`

判定：v2412 profile 可以生成 OpenFOAM native sampling artifacts。当前只检查存在性、数量和时间目录，不声明 VTP 内部字段值与 Python gauge postprocess 的逐值 parity。

## Full-horizon runtime

- config: `configs/openfoam/dam_break_vof_free_surface/full_horizon_wsl_v2412.yaml`
- result root: `_results/openfoam/dam_break_vof_free_surface/full_horizon_wsl_v2412/`
- gate: `integration`
- status: `passed`
- final time: `1.0`
- max Courant: `0.986958`
- max alpha Courant: `0.819144`
- alpha min/max: `-1.43899e-08` / `1.0`
- final water-volume relative error: `-0.018360229072319184`
- final front x: `0.5769473547499999`
- time-history rows: `11`

判定：full-horizon 本机 v2412 runtime 已通过配置内的 alpha boundedness、water-volume、front-position、artifact completeness 与 final-time gate。

## 状态结论

C06 现在已经从“v2112 本地 benchmark matrix”扩展到 v2412 sampling artifact 与 full-horizon runtime 证据。仍不能把这条证据称为外部 double-v：缺少实验 dam-break front/reference pressure 对比，也没有解析 VTP 内容做 native sampling 数值 parity。
