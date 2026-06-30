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
- conservation artifact: `postprocess/conservation_summary.json` is now generated as an open-domain inventory-change proxy.

## Failed Checks

- max Courant: `0.666666` vs threshold `0.2` -> failed. The first reported time step exceeds the configured C08 limit even though later values mostly sit near the target range.
- shock position from current centerline sampling: `0.425 m`.
- pressure jump ratio: `0.7826258811868254` -> failed shock sanity because a shock metric window should report a ratio greater than `1.0`.
- density jump ratio: `0.8622630154451846` -> failed shock sanity because a shock metric window should report a ratio greater than `1.0`.
- mass inventory relative change: `0.7925244607957768` vs threshold `0.02` -> failed. This is an open-domain inventory proxy, not a closed-control-volume flux balance.
- energy inventory proxy relative change: `0.6155462827573055` vs threshold `0.05` -> failed. This is an open-domain inventory proxy until boundary-flux integration exists.

## Status Conclusion

The OpenFOAM solver runtime path is executable and reaches the configured final time. Runtime shock and conservation artifacts are now emitted, but C08 still fails validation because CFL, shock jump sanity, and conservation proxy gates fail. C08 remains `package_skeleton_created`; do not promote it to `benchmark_validated`.

## Next Work

- Run the reduced-CFL config and require the first reported Courant number to satisfy the configured threshold rather than relaxing `max_courant`.
- Move shock sampling windows or add a more defensible shock-line extraction so pressure and density jumps are greater than `1.0` before any reference comparison.
- Replace the open-domain inventory proxy with boundary-flux mass and energy balance before any double-v promotion.
