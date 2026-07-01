# OpenFOAM C08 reduced-CFL runtime smoke

## Scope

- capability: `C08_compressible_shock_capturing_forward_step`
- gate: `smoke`
- status: `passed`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- config: `configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml`
- result root: `_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced`

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

## Face-Field Flux Parity

- method: `face_field_integration`
- included patches: `inlet`, `outlet`, `bottom`, `top`, `obstacle`
- mass imbalance: `0.025244076037939014`
- total-energy imbalance: `0.011272779328549172`
- field sources: `8` boundaryField values and `12` explicit owner-cell fallbacks
- numeric source artifact: `postprocess/face_flux_parity_summary.csv`
- status: passed for smoke-level face-field parity artifact completeness

## Status Conclusion

The reduced-CFL runtime smoke now closes the previous C08 card blockers for local solver execution, max-Courant control, leading-shock jump sanity, smoke-level accepted-baseline reference targets, boundary-flux owner-cell proxy completeness, and face-field flux integration artifact completeness. C08 still must not be promoted to `benchmark_validated` because the configured shock-position and jump targets are local smoke samples, not external or independently reviewed references, and flux evidence is not native OpenFOAM `rhoPhi/phi` functionObject parity.

## Remaining Work

- Replace the local smoke reference targets with external or independently reviewed shock position, pressure jump, and density jump references before benchmark promotion.
- Add native OpenFOAM flux parity if benchmark promotion requires native `rhoPhi/phi` evidence beyond the current face-field integration artifact.
- Add a separate downstream/reflected-compression metric if that structure is required beyond the leading-shock smoke gate.
