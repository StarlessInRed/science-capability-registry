# OpenFOAM C03 benchmark validation report

## Scope

- capability: C03_backward_facing_step_rans_internal_flow
- gate: integration
- matrix status: passed
- runtime profile: openfoam_com_v2112
- WSL distro: Ubuntu-24.04
- benchmark summary: _results\openfoam\backward_facing_step_rans_internal_flow\benchmark_matrix\case_summary.csv

## Case Matrix

- baseline_wsl_v2112: Uin=10, Re_H=25400, mesh_scale=1, pressure_drop=11.626448689110163, validation=True
- mesh_refined_wsl_v2112: Uin=10, Re_H=25400, mesh_scale=1.5, pressure_drop=9.912575957130482, validation=True
- inlet_velocity_high_wsl_v2112: Uin=15, Re_H=38100, mesh_scale=1, pressure_drop=26.845949494547177, validation=True
- inlet_velocity_low_wsl_v2112: Uin=7.5, Re_H=19050, mesh_scale=1, pressure_drop=6.360619399762921, validation=True

## Trend Checks

- trend.mesh_refined.pressure_drop_same_order: passed; mesh_drop=9.91258, baseline=11.6264
- trend.inlet_velocity_high.pressure_drop_increases: passed; high_drop=26.8459, baseline=11.6264
- trend.inlet_velocity_low.pressure_drop_decreases: passed; low_drop=6.36062, baseline=11.6264
- trend.inlet_velocity.speed_response: passed; low=7.95365, baseline=10.5816, high=15.8534

## Numeric Artifacts

- case summary CSV: _results\openfoam\backward_facing_step_rans_internal_flow\benchmark_matrix\case_summary.csv
- plot: _results\openfoam\backward_facing_step_rans_internal_flow\benchmark_matrix\plots\pressure_drop_vs_inlet_velocity.png
- plot: _results\openfoam\backward_facing_step_rans_internal_flow\benchmark_matrix\plots\lower_wall_shear_comparison.png

## Status Conclusion

The four-case local WSL v2112 matrix passed solver health, Python field postprocess, artifact completeness, and pressure/velocity trend checks. This supports benchmark_validated status for the registry-local OpenFOAM.com v2112 C03 scope.

## Residual Risk

- Evidence is local OpenFOAM.com v2112 only; Foundation/OpenFOAM-dev compatibility is not covered.
- The wall shear and yPlus outputs are Python near-wall proxy metrics because this local OpenFOAM.com v2112 WSL profile triggers a sha1 IO error, including ext4 probe paths.
- This is not an external Pitz & Daily experimental validation or mesh-independent RANS study.
