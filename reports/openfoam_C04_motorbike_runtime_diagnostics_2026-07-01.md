# OpenFOAM C04 motorBike runtime diagnostics

Date: 2026-07-01

## Scope

This report records local WSL OpenFOAM.com v2112 diagnostics for `cfd.openfoam.external_aero_motorbike_rans_snappy`.

It does not promote C04 to benchmark validation. The diagnostics split three previously coupled blockers:

- native `forceCoeffs` startup and local v2112 `sha1` IO behavior;
- solver-only `simpleFoam` stability without force/yPlus functionObjects;
- snappyHexMesh mesh quality, especially the `checkMesh` skewness gate.

## Code And Config Changes

- `runner.py` now applies the declared C04 `mesh.snappy` fields to `system/snappyHexMeshDict` instead of leaving YAML mesh settings as inert metadata.
- `runner.py` conditionally injects `#include "forceCoeffs"` only when `function_objects.force_coefficients.enabled` is true.
- `runtime.py` parses the OpenFOAM.com v2112 `checkMesh` line `Mesh non-orthogonality Max: ...` and records `max_aspect_ratio`.
- `validation.py` treats forceCoeffs and yPlus as required only when the config declares them required.
- `runtime_solver_only_wsl_v2112.yaml` disables force/yPlus to isolate the solver path.
- `runtime_layer0_solver_only_wsl_v2112.yaml` additionally disables layer addition and limits the smoke run to five simpleFoam iterations.

## Runtime Evidence

### Native forceCoeffs smoke

- Config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112.yaml`
- Evidence root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_smoke_wsl_v2112`
- Result: failed.
- Interpretation: the case reaches `checkMesh`, then `simpleFoam` fails during native forceCoeffs/functionObject startup with `FOAM FATAL IO ERROR` / `IOstream "sha1"`. Because `postProcess -func yPlus` is later in the command sequence, this run does not test native yPlus.

### Solver-only smoke

- Config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_solver_only_wsl_v2112.yaml`
- Evidence root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_solver_only_wsl_v2112`
- Result: failed.
- Runtime split: no `sha1` failure occurs after forceCoeffs is disabled. `simpleFoam` starts and advances through residual iterations, then diverges near `Time = 28` and exits with floating point exception.
- Key metrics: `cell_count=353847`, `max_non_orthogonality=65.0165`, `max_aspect_ratio=41.1519`, `max_skewness=7.64875`, `max_final_residual=2.96129e+85`.
- Interpretation: native forceCoeffs is not the only C04 blocker. With functionObjects removed, the official mesh/solver setup still fails the configured mesh quality gate and long smoke stability.

### Layer-disabled solver-only smoke

- Config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_solver_only_wsl_v2112.yaml`
- Evidence root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_solver_only_wsl_v2112`
- Result: failed overall, but the solver startup sub-gate passes.
- Key metrics: `cell_count=325757`, `max_non_orthogonality=64.9558`, `max_aspect_ratio=11.4218`, `max_skewness=7.64875`, `max_final_residual=0.0923219`.
- Passing sub-gates: all commands return 0, `simpleFoam` reaches the configured five-iteration end time, no fatal solver error is detected, and force/yPlus are correctly marked `not_required`.
- Failing sub-gates: `checkMesh` still reports failed mesh quality because `max_skewness=7.64875` exceeds the configured threshold `4.0`.
- Interpretation: disabling `addLayers` reduces aspect ratio but does not fix the highly skew face count. The current skewness is not caused solely by boundary-layer extrusion.

### Coarse refinement probe

- Probe: in-memory config derived from `runtime_layer0_solver_only_wsl_v2112.yaml` with surface refinement `[4,5]`, feature level `5`, and refinement box level `3`.
- Evidence root: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_coarse45_solver_only_probe`
- Result: failed and not promoted to committed config.
- Key metrics: `cell_count=61988`, `max_non_orthogonality=64.9185`, `max_aspect_ratio=9.75026`, `max_skewness=19.2874`.
- Interpretation: simple coarsening worsens skewness. The next mesh work should focus on snap/local geometry controls instead of lowering refinement globally.

### Single-parameter mesh probes

These probes were run after a read-only mesh diagnosis identified highly skew faces on local motorBike wall patches rather than layer cells.

| probe | changed parameter | evidence root | result |
| --- | --- | --- | --- |
| feature5 | `feature_level: 6 -> 5` | `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_feature5_layer0_probe` | failed, `max_skewness=7.70423` |
| surface45 | `surface_refinement_level: [5,6] -> [4,5]` | `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_surface45_layer0_probe` | failed, `max_skewness=9.57791` |
| box3 | `refinement_box_level: 4 -> 3` | `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_box3_layer0_probe` | failed, `max_skewness=10.0842` |

Interpretation: none of the three minimal level-reduction probes improves the skewness gate. The next mesh change should expose snap/local-geometry controls, such as feature snapping and patch-specific handling, instead of lowering all refinement levels or raising the skewness threshold.

## Scientific Status

C04 remains `package_skeleton_created`.

The repository now has better runtime separation, but the external-aero capability is still not validated:

- mesh quality does not pass the configured smoke threshold, and simple feature/surface/box level reduction does not fix it;
- native forceCoeffs is blocked by local v2112 `sha1` IO behavior;
- native yPlus has not been reached in a passing run;
- Cd/Cl tail-window stability is unavailable;
- the passing part of `runtime_layer0_solver_only_wsl_v2112` is only a short solver-startup diagnostic.

## Next Engineering Work

1. Add a config-visible snap/local-geometry mesh probe rather than relaxing `max_skewness` or globally reducing refinement.
2. Split native force and native yPlus into separate runtime profiles only after a mesh smoke profile passes.
3. Run C04 on another OpenFOAM profile, for example OpenFOAM.com v2412, to separate local v2112 behavior from capability design.
4. Promote C04 only after `checkMesh`, `simpleFoam`, native or explicitly cross-validated force coefficients, and yPlus all pass under a non-diagnostic profile.
