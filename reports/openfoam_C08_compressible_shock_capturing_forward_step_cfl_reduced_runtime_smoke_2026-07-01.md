# OpenFOAM C08 reduced-CFL runtime smoke

## Scope

- capability: `C08_compressible_shock_capturing_forward_step`
- gate: `smoke`
- status: `passed`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- config: `configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml`
- result root: `_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced_runtime_smoke_wsl_v2112_margin`

## Runtime Outcome

- `blockMesh`: returncode `0`
- `checkMesh`: returncode `0`
- `rhoCentralFoam`: returncode `0`
- final time: `4.0`
- fatal error: absent
- max Courant: `0.0949348` vs threshold `0.1` -> passed
- field sanity: `p`, `T`, `rho`, and `U` final internal fields are finite; `p`, `T`, and `rho` remain positive.

## Shock Metrics

- sample line: centerline `y=0.5`
- shock search window: `[0.35, 0.50]`
- upstream window: `[0.30, 0.40]`
- downstream window: `[0.44, 0.55]`
- shock position: `0.425 m`
- pressure jump ratio: `7.623675555555555` -> passed sanity `> 1.0`
- density jump ratio: `3.2820011603091723` -> passed sanity `> 1.0`

## Boundary Flux Proxy

- method: `boundary_flux_owner_cell_proxy`
- included patches: `inlet`, `outlet`, `bottom`, `top`, `obstacle`
- mass imbalance proxy: `0.025242669026375803` vs threshold `0.03` -> passed
- total-energy imbalance proxy: `0.011272417945887505` vs threshold `0.02` -> passed
- numeric source artifact: `postprocess/boundary_flux_summary.csv`

## Status Conclusion

The reduced-CFL runtime smoke now closes the previous C08 card blockers for local solver execution, max-Courant control, leading-shock jump sanity, and boundary-flux proxy artifact completeness. C08 still must not be promoted to `benchmark_validated` because configured external/reference shock-position and jump targets are absent, and boundary-flux evidence is an owner-cell Python proxy rather than native OpenFOAM flux parity.

## Remaining Work

- Add configured reference targets for shock position, pressure jump, and density jump before benchmark promotion.
- Add native OpenFOAM flux parity or face-field sampling parity for the boundary-flux proxy.
- Add a separate downstream/reflected-compression metric if that structure is required beyond the leading-shock smoke gate.
