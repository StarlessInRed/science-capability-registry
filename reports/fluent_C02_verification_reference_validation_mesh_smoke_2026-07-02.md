# Fluent C02 VMFL005 Mesh Smoke

- capability: `cfd.fluent.verification_reference_validation`
- config: `configs/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke.yaml`
- package: `src/science_capability_registry/fluent/verification_reference_validation/`
- gate: `smoke`
- status: passed
- runtime evidence root: `_results/fluent/verification_reference_validation/vmfl005_poiseuille_pipe_mesh_smoke/`

## Runtime Result

The local Fluent 2025 R1/v251 batch run read a self-generated 2D axisymmetric half-domain mesh for VMFL005 and completed `mesh/check`.

| metric | value |
| --- | --- |
| Fluent return code | 0 |
| mesh cells | 1280 |
| expected cells | 1280 |
| mesh nodes | 1377 |
| minimum cell volume | 9.765625e-08 m3 |
| maximum cell volume | 9.765625e-08 m3 |
| total cell volume | 0.000125 m3 |
| Fluent warnings | 4 |
| Fluent errors | 0 |

Face zones detected by Fluent:

- `interior`: 4928
- `wall`: 160
- `axis`: 160
- `pressure-outlet`: 32
- `velocity-inlet`: 32

## Scientific Boundary

This evidence closes the C02 self-generated mesh-readability blocker. It does not close the VMFL005 pressure-drop benchmark.

The current runtime intentionally stops after reading the mesh and running `mesh/check`. Fluent reports axis-boundary warnings because the solver model is not yet switched to axisymmetric before mesh import. These warnings are recorded under the configured warning budget and are treated as a remaining setup-closure task, not as pressure-drop validation evidence.

The Hagen-Poiseuille reference target remains:

- computed formula pressure drop: `10.24 Pa`
- verification manual Fluent table value: `10.22 Pa`
- manual relative error against target: `0.001953125`

## No Claims

- No local official `poiseuille-flow.cas` payload is claimed.
- No Fluent pressure-drop solve is claimed by this smoke.
- No benchmark promotion is claimed until axisymmetric setup, inlet velocity profile, pressure sampling, and mesh-trend closure pass.
