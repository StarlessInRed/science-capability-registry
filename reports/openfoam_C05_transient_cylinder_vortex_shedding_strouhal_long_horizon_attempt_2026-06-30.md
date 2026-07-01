# OpenFOAM C05 Strouhal 长时域验证尝试 - 2026-06-30

## 范围

本报告记录 `cfd.openfoam.transient_cylinder_vortex_shedding` 在本机 OpenFOAM.com v2112 / WSL 上的 Python patch-surface force proxy 长时域 Strouhal 验证尝试。

- config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112.yaml`
- corrected result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112_20260630_003/`
- diagnostic failed result root: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112_20260630_002/`
- backend: WSL Ubuntu-24.04
- OpenFOAM profile: OpenFOAM.com v2112
- solver: `pimpleFoam`
- force extraction source: `python_patch_surface_proxy`

## 关键修正

早期 C05 config 将官方 `cylinder2D` template 误标为 `D=1 m`、厚度 `1 m`、大域 `[-15, 30] x [-15, 15]`。实际由生成后的 `polyMesh` 读取得到：

- cylinder diameter: approximately `0.12 m`
- 2D thickness: approximately `0.015 m`
- domain x range: approximately `[-0.6075, 1.120002]`
- domain y range: approximately `[-0.6, 0.6]`

因此本次将 C05 configs 修正为官方 template 的实际几何尺度，并将 Re=100 long-horizon config 设置为：

- `U = 1 m/s`
- `D = 0.12 m`
- `nu = 0.0012 m2/s`
- `end_time_s = 8`
- `write_interval_s = 0.025`
- `adjustTimeStep = yes`
- `maxCo = 0.5`
- `maxDeltaT = 0.001`

同时 validation 增加 force sample count、force time span、finite value、lift peak count、period coefficient of variation、lift amplitude 和 frequency-method cross-check 等质量门槛，并将 final-time 检查改为允许一个配置时间步量级的尾差。

## 结果

修正几何后的 `_003` runtime 未通过 integration gate，但失败已收敛为 Strouhal target mismatch。

- `./Allrun.pre` return code: `0`
- `pimpleFoam` return code: `0`
- final time: `7.999830037232331`
- max Courant number: `0.4933629867730591`
- max final residual: `0.005050025490524501`
- force coefficient rows: `320`
- force time span: `7.975000000232331 s`
- nonfinite force rows: `0`
- Strouhal available: `true`
- analysis window: `6 s`
- analysis rows: `240`
- lift peak count: `7`
- mean period: `0.8666666666668581 s`
- period CV: `0.01359820733058574`
- primary method: `lift_peak_period`
- primary estimated Strouhal: `0.13846153846150788`
- cross-check method: `lift_fft`
- cross-check estimated Strouhal: `0.13999999999997378`
- frequency relative delta: approximately `0.0111`
- configured target range: `[0.16, 0.24]`
- validation status: failed
- failed check after refreshed postprocess: `postprocess.strouhal_target_range`

The earlier `_002` diagnostic run is retained as failure evidence for the geometry-scale error: it used config `D=1` against the actual `D≈0.12` mesh, reached final time 30 s, but failed `solver.max_courant` and produced a nonsensical Strouhal estimate under the wrong reference diameter.

## 判定

C05 已关闭三个工程卡点：

- local WSL runtime 可以完成 long-horizon `pimpleFoam` 求解并生成 force CSV。
- config 中的 official template 几何尺度已修正为与生成 mesh 一致。
- 当前 `_003` 证据已由最新 postprocess/validation 刷新，`lift_peak_period` 与 `lift_fft` 均可用且相互一致。

但 C05 仍不能进入 benchmark validation：

- native OpenFOAM `forceCoeffs` 仍被 local v2112 WSL `sha1` IO behavior 阻断。
- Python patch-surface proxy 的 Strouhal estimate 低于当前 `0.16-0.24` target range。
- 还没有 native forceCoeffs parity、DMD frequency parity、mesh/time-step sensitivity 或外部 reference comparison。

因此 `benchmark_status` 保持 `validation_failed`，直到 Strouhal reference、force extraction parity 和敏感性矩阵被进一步闭合。

## 后续任务

1. 用 official DMD output 或可运行的 native force coefficient path 交叉验证 shedding frequency。
2. 判断当前 official `cylinder2D` template 在该域尺寸、Re=100、Python proxy 下的合理 Strouhal target 是否应独立定义。
3. 添加 time-step sensitivity 和 mesh sensitivity 配置，只在 Strouhal target 有依据后再做 benchmark promotion。
4. 保留 Python proxy 为诊断路径，但不能用它单独证明 benchmark-grade force coefficient 或 Strouhal。
