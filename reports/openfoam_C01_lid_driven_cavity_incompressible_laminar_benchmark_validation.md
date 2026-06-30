# OpenFOAM C01 benchmark validation report

## Scope

- capability: `C01_lid_driven_cavity_incompressible_laminar`
- gate: `integration`
- matrix status: `passed`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- benchmark summary: `_results\openfoam\lid_driven_cavity_incompressible_laminar\benchmark_matrix\case_summary.csv`

## Case Matrix

- `baseline_wsl_v2112`: Re=10, mesh=[20, 20, 1], dt=0.005, maxCo=0.852134, validation=True
- `mesh_40x40_cfl_matched_wsl_v2112`: Re=10, mesh=[40, 40, 1], dt=0.0025, maxCo=0.926451, validation=True
- `re100_wsl_v2112`: Re=100, mesh=[40, 40, 1], dt=0.00125, maxCo=0.460958, validation=True
- `dt_half_wsl_v2112`: Re=10, mesh=[20, 20, 1], dt=0.0025, maxCo=0.426065, validation=True

## Trend Checks

- `trend.mesh_refinement.centerline_similarity`: passed; vertical_Ux_MAE=0.0139675, horizontal_Uy_MAE=0.00802615, threshold=0.08
- `trend.dt_half.centerline_similarity_and_courant_drop`: passed; vertical_Ux_MAE=8.62143e-06, horizontal_Uy_MAE=6.53571e-06, maxCo=0.426065 < baseline 0.852134
- `trend.re100.stronger_velocity_gradients`: passed; vertical_gradient_ratio=1.19725, horizontal_gradient_ratio=1.13906, threshold=1.05

## Numeric Artifacts

- case summary CSV: `_results\openfoam\lid_driven_cavity_incompressible_laminar\benchmark_matrix\case_summary.csv`
- plot: `_results\openfoam\lid_driven_cavity_incompressible_laminar\benchmark_matrix\plots\vertical_centerline_Ux_comparison.png`
- plot: `_results\openfoam\lid_driven_cavity_incompressible_laminar\benchmark_matrix\plots\horizontal_centerline_Uy_comparison.png`

## Status Conclusion

The four-case matrix, solver health checks, centerline CSV artifacts, trend checks, and plots passed. This supports promoting `benchmark_status` to `benchmark_validated`.

## Residual Risk

- Evidence is from local WSL OpenFOAM.com v2112 only; Foundation OpenFOAM is not covered by this report.
- Trend checks are based on official tutorial physics and local perturbations, not on an external high-accuracy Ghia-style reference dataset.
