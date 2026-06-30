# OpenFOAM C06 benchmark validation report

## Scope

- capability: C06_dam_break_vof_free_surface
- gate: integration
- matrix status: passed
- runtime profile: openfoam_com_v2112
- WSL distro: Ubuntu-24.04
- benchmark summary: _results\openfoam\dam_break_vof_free_surface\benchmark_matrix\case_summary.csv

## Case Matrix

- baseline_wsl_v2112: g=9.81, h0=0.292, mesh_scale=1, front_x=0.24756521739999998, volume_error=-1.3011760106366253e-07, validation=True
- mesh_refined_wsl_v2112: g=9.81, h0=0.292, mesh_scale=1.5, front_x=0.2404299398, volume_error=-3.0968999924197594e-07, validation=True
- gravity_half_wsl_v2112: g=4.905, h0=0.292, mesh_scale=1, front_x=0.2094782609, volume_error=-8.168176655022503e-08, validation=True
- water_height_125pct_wsl_v2112: g=9.81, h0=0.365, mesh_scale=1, front_x=0.24756521739999998, volume_error=-1.0777392843908812e-07, validation=True

## Trend Checks

- trend.mesh_refined.front_same_order: passed; mesh_front=0.24043, baseline=0.247565
- trend.gravity_half.front_slower: passed; gravity_front=0.209478, baseline=0.247565
- trend.water_height_125pct.volume_increases: passed; height_volume=0.000816415, baseline=0.000646099
- trend.water_height_125pct.front_not_slower: passed; height_front=0.247565, baseline=0.247565

## Numeric Artifacts

- case summary CSV: _results\openfoam\dam_break_vof_free_surface\benchmark_matrix\case_summary.csv
- plot: _results\openfoam\dam_break_vof_free_surface\benchmark_matrix\plots\front_position_history.png
- plot: _results\openfoam\dam_break_vof_free_surface\benchmark_matrix\plots\water_volume_error_history.png

## Status Conclusion

The four-case local WSL v2112 matrix passed solver health, alpha boundedness, water-volume, front-propagation, artifact, and perturbation trend checks for the registry-local C06 scope.

## Residual Risk

- Evidence is local OpenFOAM.com v2112 only.
- The horizon is the configured short integration horizon, not a full experimental dam-break reference comparison.
- The OpenFOAM sampling functionObject is disabled because this local OpenFOAM.com v2112 WSL profile triggers a sha1 IO error, including ext4 probe paths; Python alpha-field postprocess is used instead.
- This is laminar interFoam VOF only; RAS damBreak and four-phase tutorials are out of scope.
