# OpenFOAM C08 runtime smoke attempt

## Scope

- capability: `C08_compressible_shock_capturing_forward_step`
- gate: `smoke` attempt plus shock-validation readiness
- matrix status: `failed`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- result root: `_results/openfoam/compressible_shock_capturing_forward_step/baseline_runtime_smoke_wsl_v2112`

## Runtime Outcome

- `blockMesh`: returncode `0`
- `checkMesh`: returncode `0`
- `rhoCentralFoam`: returncode `0`
- final time: `4.0`
- fatal error: absent
- field sanity: `p`, `T`, `rho`, and `U` internal fields are finite; `p`, `T`, and `rho` are positive in the final written field.

## Failed Checks

- max Courant: `0.666666` vs threshold `0.2` -> failed. The first reported time step exceeds the configured C08 limit even though later values mostly sit near the target range.
- shock metrics: unavailable because runtime shock-line sampling is not implemented yet.
- conservation metrics: unavailable for mass and energy proxy.
- required artifacts missing: `postprocess/shock_line_samples.csv`, `postprocess/shock_metrics.json`.

## Status Conclusion

The OpenFOAM solver runtime path is executable and reaches the configured final time, but C08 still fails validation because CFL, shock sampling, and conservation gates are incomplete. C08 remains `package_skeleton_created`; do not promote it to `benchmark_validated`.

## Next Work

- Add runtime sampling or field-slice extraction for pressure/density shock-line metrics.
- Decide whether the initial Courant overshoot should be treated as a hard failure, ignored warm-start transient, or fixed by the reduced-CFL config.
- Add conservation metrics before any double-v promotion.
