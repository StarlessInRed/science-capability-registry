# OpenFOAM C02/C04/C07/C08 runtime closure execution

日期：2026-07-01

## 结论

本轮不是把任务放入 TODO，而是完成了本机 OpenFOAM.com v2112/v2412 能执行的 runtime 复测和证据分类。未通过项保留为 failed evidence，不提升 `benchmark_status`。

## C02 potentialFoam cylinder

- 执行配置：`configs/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112.yaml`
- 证据目录：`_results/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112`
- runtime 结果：`blockMesh`、`checkMesh`、`potentialFoam -writePhi -writephi -writep` 均 returncode 0。
- validation 结果：failed。
- 失败门：`velocity_l2_error=1.1647355770764016`，`velocity_linf_error=6.912121724051375`，`cp_linf_error=1.6228866742770676`；`pressure_l2_error=0.1366400904374664` 通过。
- 科学判断：当前官方有限域半圆柱 case 不能直接按无界圆柱势流解析解声明通过；不应放宽阈值掩盖 finite-domain/sampling/Cp proxy 问题。

## C04 motorBike RANS snappy

- 执行配置：`configs/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112.yaml`
- 证据目录：`_results/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112`
- 已修复 runtime 阻塞：为 6 分区 `mpirun` 增加 `--oversubscribe`，并把 processor 初始场复制命令改成不依赖 shell `$d` 展开的显式 processor0-5 复制。
- runtime 进展：`surfaceFeatureExtract`、`blockMesh`、`decomposePar`、`snappyHexMesh`、`topoSet`、`patchSummary`、`potentialFoam`、`checkMesh` 均 returncode 0。
- validation 结果：failed。
- 失败门：`simpleFoam` returncode 1，v2112 日志报 `FOAM FATAL IO ERROR` / `sha1`；`checkMesh` 同时报告 mesh failed，`max_skewness=7.64875`，超过配置阈值 4.0。
- 科学判断：C04 已从 static readiness 推进到真实 runtime failed evidence；Cd/Cl、forceCoeffs tail-window 和 y+ 不能声明完成。

## C07 conjugate heat transfer

- 执行配置：`configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml --backend wsl`
- 证据目录：`_results/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112`
- runtime 结果：`./Allrun.pre`、`checkMesh -allRegions -constant`、`faceAgglomerate`、`viewFactorsGen`、`chtMultiRegionSimpleFoam` 均 returncode 0。
- validation 结果：passed，`benchmark_status=runtime_smoke_verified`。
- 关键指标：final time `2.0`，max final residual `0.08369737`，5 个 region 均出现，region temperature bounds 通过。
- promotion guard：heat-flux 仍是 Python paired-patch owner-cell proxy；未形成 native/interface heat-flux conservation、区域能量平衡或外部 reference，因此不提升到 benchmark_validated。

## C08 forwardStep shock

- 执行配置：`configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml --backend wsl`
- 证据目录：`_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced`
- runtime 结果：`blockMesh`、`checkMesh`、`rhoCentralFoam` 均 returncode 0。
- validation 结果：passed。
- 关键指标：final time `4.0`，max Courant `0.0949348`，shock position `0.425`，pressure jump ratio `7.623675555555555`，density jump ratio `3.2820011603091723`。
- conservation proxy：boundary mass imbalance proxy `0.025242669026375803`，total-energy imbalance proxy `0.011272417945887505`，均通过当前 smoke 阈值。
- promotion guard：flux 仍是 owner-cell Python proxy，shock reference 是配置内 accepted baseline，不是独立外部 reference；保持 smoke，不提升 benchmark。

## C05 Strouhal cross-check

- 证据目录：`_results/openfoam/transient_cylinder_vortex_shedding/runtime_python_force_proxy_strouhal_wsl_v2112_20260630_003`
- runtime 结果：`pimpleFoam` returncode 0，final time `7.999830037232331`，max Courant `0.4933629867730591`。
- validation 结果：failed。
- 失败门：Strouhal `0.13846153846150788`，低于目标区间 `[0.16, 0.24]`；force samples、time span、peak count、period CV、lift amplitude 均通过。
- 科学判断：当前问题是 shedding-frequency/reference parity，不是 solver wiring；不能通过调整目标区间闭环。

## C01/C03/C06 cross-profile replay

- C01、C03、C06 均已修复 numbered log artifact contract，并完成 v2112/v2412 replay。
- C01 v2112/v2412：validation passed，final time `0.5`，max Co `0.852134`。
- C03 v2112/v2412：validation passed，final pseudo-time `80.0`，pressure drop v2112 `11.626448689110163`，v2412 `11.49693043511933`。
- C06 v2112/v2412：validation passed，final time `0.1`，max Co `0.95975`，alpha volume relative error `-1.3011760106366253e-07`。

## 当前状态

| 能力 | 本轮状态 | 是否提升 benchmark |
| --- | --- | --- |
| C01 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C02 | runtime completed, analytical gates failed | 否 |
| C03 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C04 | runtime executed to simpleFoam/mesh-quality failed evidence | 否 |
| C05 | long-horizon solver/proxy passed, Strouhal gate failed | 否 |
| C06 | v2112/v2412 replay passed | 否，保持 `benchmark_validated` |
| C07 | MHR runtime smoke passed with proxy heat flux | 否，保持 `benchmark_candidate` |
| C08 | reduced-CFL shock smoke passed | 否，保持 `package_skeleton_created` |
