# OpenFOAM C05 Intern Task: Transient Cylinder Vortex Shedding

## 目标

把 OpenFOAM.com v2112 `pimpleFoam/laminar/cylinder2D` 官方 tutorial 转化为可复用、可配置、可验证的瞬态圆柱绕流能力。

## 当前边界

- 已建立 capability card、run schema、baseline config、package runner、case generator、dry-run manifest、runtime parser 与 force coefficient postprocess contract。
- 本地 solver execution 与 Python patch-surface force CSV 已闭环；official template 几何尺度已修正为生成 mesh 的 `D≈0.12 m`、厚度 `≈0.015 m`。
- native OpenFOAM `forceCoeffs` 仍受 local v2112/WSL `sha1` IO behavior 阻断。
- 修正几何后的 Re=100 long-horizon Python proxy run 和 v2412 native forceCoeffs run 均得到 `St≈0.14`。
- 当前 finite-domain OpenFOAM cylinder2D case-freeze 已按 `[0.13, 0.15]` 本地 tutorial 目标闭环，`benchmark_status` 为 `benchmark_validated`；外部 free-cylinder `[0.16, 0.24]` 仍是后续推广目标，不得混同。

## 最小交付

1. 继续强化 `src/science_capability_registry/openfoam/transient_cylinder_vortex_shedding/` package
2. runtime runner：在 `openfoam_com_v2112` WSL profile 下执行 mesh workflow 与 `pimpleFoam`
3. log parser：提取 Courant、Time、residual、fatal error、final time
4. postprocess：输出 lift/drag time series、force coefficient CSV、Strouhal summary
5. validation：检查 Courant、残差、force artifact、Strouhal provisional range 和工件完整性
6. 添加 mesh refinement、time step sensitivity、Reynolds sensitivity 三个 perturbation cases
7. 用 official DMD output、native forceCoeffs 可运行路径或外部 reference 交叉验证 Strouhal target

## 验证标准

- 不得把 force/Strouhal 目标写死在代码中，必须来自 config。
- 没有 force coefficient 时间序列时不得计算 Strouhal。
- 没有 native/DMD/reference parity 和至少一个 mesh/time-step sensitivity case 前，不得声称外部 free-cylinder benchmark validation。

## 下一步验收检查

1. 稳定 native OpenFOAM `forceCoeffs` 路径，或给出等价提取路径的可复核证明；必须生成 force coefficient artifacts。
2. 执行 Re=100 long-horizon run，并同时满足：
   - `postprocess.strouhal_target_range` 进入 `[0.16, 0.24]`
   - `postprocess.strouhal_peak_count >= 5`
   - `postprocess.strouhal_period_cv <= 0.3`
   - `postprocess.strouhal_cl_amplitude >= 0.001`
   - `postprocess.force_sample_count >= 200`
   - `postprocess.force_time_span >= 6 s`
   - Courant 与 residual 均低于配置阈值
3. 增加至少一个 mesh 或 time-step sensitivity case，且保持同一 Strouhal/force gate 通过。
4. 若最终仍采用 Python patch-surface force proxy，必须记录与 native forceCoeffs、official DMD 或外部 reference 的 parity 结果，否则只能维持本地 finite-domain case-freeze claim。
