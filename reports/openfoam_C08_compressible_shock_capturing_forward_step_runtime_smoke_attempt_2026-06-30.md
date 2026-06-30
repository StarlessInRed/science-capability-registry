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
- shock-line artifacts: `postprocess/shock_line_samples.csv` and `postprocess/shock_metrics.json` are now generated from Python cell-centre line sampling of the final OpenFOAM fields.
- conservation artifacts: `postprocess/conservation_summary.json` is now generated as a boundary-flux owner-cell proxy; `postprocess/boundary_flux_summary.csv` is the required numeric source artifact for patch flux terms in fresh runs.

## Failed Checks

- max Courant: `0.666666` vs threshold `0.2` -> failed. The first reported time step exceeds the configured C08 limit even though later values mostly sit near the target range.
- shock position from the old unrestricted centerline gradient search: `0.425 m`.
- pressure jump ratio from the old windows `[1.0, 1.2] -> [1.4, 1.6]`: `0.7826258811868254` -> failed shock sanity because that window pair straddled the wrong downstream state.
- density jump ratio from the old windows `[1.0, 1.2] -> [1.4, 1.6]`: `0.8622630154451846` -> failed shock sanity for the same reason.
- boundary-flux owner-cell proxy is now the canonical conservation artifact for C08, but this report predates a fresh runtime using the updated flux-proxy validation keys.

## Status Conclusion

The OpenFOAM solver runtime path is executable and reaches the configured final time. C08 now has a more defensible leading-shock search window and a boundary-flux owner-cell proxy design, but it still needs a fresh reduced-CFL runtime to close max-Courant and flux-proxy validation. C08 remains `package_skeleton_created`; do not promote it to `benchmark_validated`.

## Next Work

- Run the reduced-CFL config with `deltaT=0.0002` and solver target `maxCo=0.09`, while keeping the validation threshold at `max Courant <= 0.1`.
- Keep the leading-shock metric on `shock_search_window_m: [0.35, 0.50]`, `upstream_window_m: [0.30, 0.40]`, and `downstream_window_m: [0.44, 0.55]`.
- Compare the boundary-flux owner-cell proxy against native OpenFOAM flux output or face-field sampling before any double-v promotion.
