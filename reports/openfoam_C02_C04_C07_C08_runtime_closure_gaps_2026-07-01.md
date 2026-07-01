# OpenFOAM C02/C04/C05/C07/C08 runtime closure execution

日期：2026-07-01

## 结论

本轮不是把任务放入 TODO，而是完成了本机 OpenFOAM.com v2112/v2412 能执行的 runtime 复测和证据分类。未通过项保留为 failed evidence，不提升 `benchmark_status`。

## C02 potentialFoam cylinder

- 严格解析配置：`configs/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112.yaml`
- 严格证据目录：`_results/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112`
- 严格 runtime 结果：`blockMesh`、`checkMesh`、`potentialFoam -writePhi -writephi -writep` 均 returncode 0。
- 严格 validation 结果：failed。
- 严格失败项：`velocity_l2_error=1.1647355770764016`，`velocity_linf_error=6.912121724051375`，`cp_linf_error=1.6228866742770676`；`pressure_l2_error=0.1366400904374664` 通过。
- 新增诊断配置：`configs/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112.yaml`
- 新增诊断证据目录：`_results/openfoam/potential_flow_cylinder_analytical_validation/finite_domain_diagnostic_wsl_v2112`
- 新增诊断 validation 结果：passed。
- 科学判定：当前官方有限域半圆柱 case 不能直接按无界圆柱势流解析解声明通过；finite-domain diagnostic 只证明 solver、artifact 和误差提取链路可执行，不证明严格 analytical benchmark。

## C04 motorBike RANS snappy

- 原 runtime 配置：`configs/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112.yaml`
- 原证据目录：`_results/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112`
- 已修复 runtime 阻塞：为 6 分区 `mpirun` 增加 `--oversubscribe`，并将 processor 初始场复制命令改成显式 `processor0-5` 复制。
- 原 runtime 进展：`surfaceFeatureExtract`、`blockMesh`、`decomposePar`、`snappyHexMesh`、`topoSet`、`patchSummary`、`potentialFoam`、`checkMesh` 均 returncode 0。
- 原 validation 结果：failed。
- 原失败项：`simpleFoam` returncode 1，v2112 日志报告 `FOAM FATAL IO ERROR` / `sha1`；`checkMesh` 同时报告 mesh failed，`max_skewness=7.64875`，超过配置阈值 `4.0`。
- 新增 solver-only 配置：`runtime_solver_only_wsl_v2112.yaml` 和 `runtime_layer0_solver_only_wsl_v2112.yaml`。
- 新增诊断结果：禁用 force/yPlus 后不再触发 `sha1`；layer-disabled solver-only 短程 `simpleFoam` 5 步 returncode 0，max residual `0.0923219`。
- 仍未关闭项：mesh skewness 仍为 `7.64875`，超过 smoke 阈值；native forceCoeffs 和 yPlus 仍未验证。
- 科学判定：C04 已从 static readiness 推进到真实 runtime failed evidence；Cd/Cl、forceCoeffs tail-window 和 y+ 不能声明完成。

## C05 transient cylinder Strouhal

- 配置：`configs/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112.yaml`
- 证据目录：`_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112_20260630_003`
- runtime 结果：`pimpleFoam` returncode 0，final time `7.999830037232331`，max Courant `0.4933629867730591`。
- refreshed validation 结果：failed。
- 通过项：force samples `320`，force time span `7.975000000232331 s`，lift peak count `7`，period CV `0.01359820733058574`，lift amplitude finite，`lift_fft` cross-check available。
- 频率结果：primary `lift_peak_period` gives `St=0.13846153846150788`; cross-check `lift_fft` gives `St=0.13999999999997378`。
- 唯一失败项：`postprocess.strouhal_target_range`，低于目标区间 `[0.16, 0.24]`。
- 科学判定：当前问题不是 solver wiring 或旧字段缺失，而是 shedding-frequency/reference parity；不应通过放宽目标区间闭环。

## C07 conjugate heat transfer

- 配置：`configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml --backend wsl`
- 证据目录：`_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112`
- runtime 结果：`./Allrun.pre`、`checkMesh -allRegions -constant`、`faceAgglomerate`、`viewFactorsGen`、`chtMultiRegionSimpleFoam` 均 returncode 0。
- validation 结果：passed，`benchmark_status=runtime_smoke_verified`。
- 关键指标：final time `2.0`，max final residual `0.08369737`，3 个 region 均出现，region temperature bounds 通过。
- promotion guard：heat-flux 仍是 Python paired-patch owner-cell proxy；未形成 native/interface heat-flux conservation、区域能量平衡或外部 reference，因此不提升到 `benchmark_validated`。

## C08 forwardStep shock

- 配置：`configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml --backend wsl`
- 证据目录：`_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced`
- runtime 结果：`blockMesh`、`checkMesh`、`rhoCentralFoam` 均 returncode 0。
- validation 结果：passed。
- 关键指标：final time `4.0`，max Courant `0.0949348`，shock position `0.425`，pressure jump ratio `7.623675555555555`，density jump ratio `3.2820011603091723`。
- conservation proxy：boundary mass imbalance proxy `0.025242669026375803`，total-energy imbalance proxy `0.011272417945887505`，均通过当前 smoke 阈值。
- promotion guard：flux 仍是 owner-cell Python proxy，shock reference 是配置内 accepted baseline，不是独立外部 reference；保持 smoke，不提升 benchmark。

## C01/C03/C06 cross-profile replay

- C01、C03、C06 均已修复 numbered log artifact contract，并完成 v2112/v2412 replay。
- C01 v2112/v2412：validation passed，final time `0.5`，max Co `0.852134`。
- C03 v2112/v2412：validation passed，final pseudo-time `80.0`，pressure drop v2112 `11.626448689110163`，v2412 `11.49693043511933`。
- C06 v2112/v2412：validation passed，final time `0.1`，max Co `0.95975`，alpha volume relative error `-1.3011760106366253e-07`。

## 当前状态

| 能力 | 本轮状态 | 是否提升 benchmark |
| --- | --- | --- |
| C01 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C02 | strict analytical gate failed; finite-domain diagnostic passed | 否 |
| C03 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C04 | runtime failed evidence plus solver-only diagnostics | 否 |
| C05 | long-horizon solver/proxy passed; Strouhal target failed with FFT parity | 否 |
| C06 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C07 | MHR runtime smoke passed with proxy heat flux | 否，保持 `benchmark_candidate` |
| C08 | reduced-CFL shock smoke passed | 否，保持 `package_skeleton_created` |
