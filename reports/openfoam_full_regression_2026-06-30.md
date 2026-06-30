# OpenFOAM full-regression summary

## Scope

- date: 2026-06-30
- repository area: OpenFOAM capability registry assets and shared runtime helpers
- gate: `full-regression`
- runtime profile checked: `openfoam_com_v2112`
- backend: WSL `Ubuntu-24.04`

## Static And Unit Gate

Command:

```bat
Tools\python.bat -m pytest
```

Result:

- `68 passed`
- OpenFOAM subset: `34 passed`
- Cantera tests also passed, so the shared OpenFOAM helper changes did not regress existing Cantera capability tests.

## Runtime Smoke Gate

| capability | config | output evidence | result | key metrics |
| --- | --- | --- | --- | --- |
| C01 lid-driven cavity | `configs/openfoam/lid_driven_cavity_incompressible_laminar/baseline_wsl_v2112.yaml` | `_results/openfoam/lid_driven_cavity_incompressible_laminar/fullreg_c01_profile/` | passed | `blockMesh=0`, `checkMesh=0`, `icoFoam=0`, final time `0.5`, max Courant `0.852134` |
| C03 backward-facing step | `configs/openfoam/backward_facing_step_rans_internal_flow/baseline_wsl_v2112.yaml` | `_results/openfoam/backward_facing_step_rans_internal_flow/fullreg_c03_profile/` | passed | `blockMesh=0`, `checkMesh=0`, `simpleFoam=0`, final pseudo-time `80`, max final residual `0.00154837`, pressure drop `11.626448689110163` |
| C06 dam break VOF | `configs/openfoam/dam_break_vof_free_surface/baseline_wsl_v2112.yaml` | `_results/openfoam/dam_break_vof_free_surface/fullreg_c06_profile/` | passed | `blockMesh=0`, `setFields=0`, `checkMesh=0`, `interFoam=0`, final time `0.1`, max Courant `0.95975`, max alpha Courant `0.822277` |

The `_results/` runtime directories are local evidence only and remain ignored by Git.

## Runtime Profile Contract

New runtime profile contract and catalog:

- schema: `schemas/openfoam_runtime_profile.schema.json`
- local profiles:
  - `configs/openfoam/runtime_profiles/openfoam_com_v2112.yaml`
  - `configs/openfoam/runtime_profiles/openfoam_com_v2412.yaml`
- loader: `src/science_capability_registry/openfoam/runtime_profiles.py`

The shared `template_case` runtime helper now resolves WSL distro, bashrc, timeout, case layout, and required executables through the config plus runtime profile. Missing runtime profile, profile/config identity conflicts, missing WSL distro or bashrc, undeclared executable overrides, and incomplete sourced OpenFOAM environment variables now fail fast instead of falling back silently to a hardcoded distro or partial runtime state.

Runtime inventory report:

- `reports/openfoam_runtime_profile_inventory_2026-06-30.md`

`openfoam_com_v2412` has bashrc, executable, and tutorial-root probe evidence. It is registered as a second OpenFOAM.com profile, but C01/C03/C06 runtime smoke evidence in this report is still from `openfoam_com_v2112`.

## sha1 Probe Result

Report:

- `reports/openfoam_runtime_profile_sha1_probe.md`

Summary:

- C03 native `simpleFoam` functionObjects and `wallShearStress/yPlus` post-processing reproduce `sha1` fatal IO errors on WSL ext4 `/tmp`.
- C06 native sampling reproduces `sha1` fatal IO errors on WSL ext4 `/tmp`.
- Therefore this is classified as a local `openfoam_com_v2112` WSL runtime-profile limitation, not merely a Windows-mounted repository-path limitation.

## Status

C01, C03, and C06 can remain `benchmark_validated` for the current registry-local `integration` evidence scope.

C03 and C06 must not be promoted to `double-v` until one of the following exists:

- native functionObject/sampling parity evidence from another working OpenFOAM runtime profile
- independent benchmark/reference comparison

## Residual Risk

- Foundation OpenFOAM and OpenFOAM-dev compatibility were not run.
- `openfoam_com_v2412` was registered from lightweight profile probes, but C01/C03/C06 solver smoke was not rerun on v2412.
- C01 still lacks external centerline reference comparison and grid/time convergence error tables.
- C03 still uses Python proxy wall shear/yPlus metrics, not native OpenFOAM functionObject outputs.
- C06 remains a short-horizon integration benchmark and does not yet cover full-horizon dam-break reference behavior.
