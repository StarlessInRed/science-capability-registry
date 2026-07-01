# OpenFOAM C04 v2412 coarse34 layer3 force/yPlus smoke - 2026-07-01

## Scope

- capability: `C04_external_aero_motorbike_rans_snappy`
- config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_coarse34_layer3_force_yplus_wsl_v2412.yaml`
- result root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_coarse34_layer3_force_yplus_wsl_v2412/`
- runtime profile: `openfoam_com_v2412`
- backend: WSL `Ubuntu-24.04`

## Result

The run closes the previous strict mesh and native forceCoeffs startup blocker for a coarse v2412 motorBike profile:

- `checkMesh`: passed
- cells: `16586`
- max non-orthogonality: `61.0152`
- max aspect ratio: `16.018`
- max skewness: `2.66334`
- highly skew faces: `0`
- `simpleFoam`: returncode `0`
- max final residual: `0.0734606`
- native `forceCoeffs`: available
- coefficient rows: `20`
- Cd tail mean/std: `0.29571504000000004` / `0.051051036508795784`
- Cl tail mean/std: `0.27280650500000003` / `0.05269450338222645`

The validation remains failed because native yPlus is outside the wall-function target:

- y+ min: `15.441`
- y+ max: `3138.67`
- y+ mean: `582.20821875`
- failed check: `yPlus.range`

## Interpretation

This evidence changes the C04 blocker from "cannot get a strict motorBike mesh/solver/force path" to "strict coarse mesh and native force path exist, but wall-function y+ is not valid." The correct next C04 task is now a wall-normal mesh/layer strategy that brings y+ into `[30, 300]` without reintroducing skewness failure.

The result is not benchmark promotion evidence. Cd/Cl values come from a 20-iteration smoke and do not prove aerodynamic coefficient convergence or reference agreement.
