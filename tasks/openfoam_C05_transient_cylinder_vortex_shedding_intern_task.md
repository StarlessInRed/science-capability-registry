# OpenFOAM C05 Intern Task: Transient Cylinder Vortex Shedding

## 目标

把 OpenFOAM.com v2112 `pimpleFoam/laminar/cylinder2D` 官方 tutorial 转化为可复用、可配置、可验证的瞬态圆柱绕流能力。

## 当前边界

- 本轮已建立 capability card、run schema 和 baseline dry-run config。
- 尚未实现 package runner、case generator、solver execution、force coefficient parser 或 Strouhal 验证。
- 因此 `benchmark_status` 必须保持 `benchmark_candidate`。

## 最小交付

1. `src/science_capability_registry/openfoam/transient_cylinder_vortex_shedding/` package
2. dry-run runner：复制官方 cylinder2D template，写出 manifest，并校验 U/p、transportProperties、controlDict、fvSchemes、fvSolution、mesh dictionaries
3. runtime runner：在 `openfoam_com_v2112` WSL profile 下执行 mesh workflow 与 `pimpleFoam`
4. log parser：提取 Courant、Time、residual、fatal error、final time
5. postprocess：输出 lift/drag time series、force coefficient CSV、Strouhal summary
6. validation：检查 Courant、残差、force artifact、Strouhal provisional range 和工件完整性

## 验证标准

- 不得把 force/Strouhal 目标写死在代码中，必须来自 config。
- 没有 force coefficient 时间序列时不得计算 Strouhal。
- 没有本地 runtime 和至少一个 mesh/time-step sensitivity case 前，不得提升为 `benchmark_validated`。
