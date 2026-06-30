# OpenFOAM C01 baseline_wsl_v2112 runtime smoke report

## 范围

- capability: `C01_lid_driven_cavity_incompressible_laminar`
- gate: `smoke`
- case: `baseline_wsl_v2112`
- config: `configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112.yaml`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- bashrc: `/opt/OpenFOAM-v2112/etc/bashrc`

本报告证明这台电脑可以执行 C01 OpenFOAM runtime smoke。完整 C01 状态以 benchmark validation report 和 full-regression summary 为准。

## 运行结果

- `blockMesh` returncode: `0`
- `checkMesh` returncode: `0`
- `icoFoam` returncode: `0`
- final time: `0.5`
- max Courant number: `0.852134`
- Courant threshold: `<= 1.0`
- residual samples: `800`
- last continuity sum local: `9.66354e-09`
- validation: `passed: true`

## 本地证据

- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/manifest.json`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/metrics.json`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/validation.json`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/validation_report.md`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/logs/log.blockMesh`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/logs/log.checkMesh`
- `_results/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112/logs/log.icoFoam`

## 当前状态

- `card_status`: `accepted`
- `benchmark_status`: `benchmark_validated`
- current evidence scope: local `openfoam_com_v2112` WSL integration matrix

## 残余风险

- 本报告是单 case smoke，不是四案例 integration matrix 本身。
- C01 still needs external centerline reference comparison before `double-v`.
- Foundation/OpenFOAM-dev compatibility has not been run.
