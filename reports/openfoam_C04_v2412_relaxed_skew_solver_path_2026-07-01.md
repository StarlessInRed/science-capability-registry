# OpenFOAM C04 v2412 relaxed-skew solver-path diagnostic

日期: 2026-07-01

## 结论

C04 motorBike 在本机 OpenFOAM.com v2412 / WSL profile 下已经证明可以进入真实 solver path: `surfaceFeatureExtract`、`blockMesh`、`snappyHexMesh`、`topoSet`、`patchSummary`、`potentialFoam`、`checkMesh -meshQuality` 和 5 步 `simpleFoam` 均返回 0。

但该结果仍是 failed smoke diagnostic，不是外流气动 benchmark。`checkMesh` 仍报告 mesh quality failed，当前卡点从 runtime/profile 问题收敛为 motorBike 局部 skewness mesh repair 问题。

## 运行证据

- Config: `configs/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_relaxed_skew_wsl_v2412.yaml`
- Output: `_results/openfoam/external_aero_motorbike_rans_snappy/runtime_layer0_relaxed_skew_wsl_v2412/`
- Runtime profile: OpenFOAM.com v2412, `Ubuntu-24.04` WSL
- Mesh quality diagnostic settings: `maxInternalSkewness=12`, `maxBoundarySkewness=20`, `minTwist=-1`

## 关键指标

- `validation.passed`: `false`
- Failed check: `mesh.checkMesh_ok`
- `cell_count`: 325743
- `max_non_orthogonality`: 64.9969
- `max_aspect_ratio`: 12.8417
- `max_skewness`: 9.89474
- `highly_skew_face_count`: 13
- `skew_face_set_count`: 13
- `solver.started`: `true`
- `solver.fatal_error_detected`: `false`
- `solver.max_final_residual`: 0.0727057
- All expected runtime artifacts and logs were emitted.

## 解释

This diagnostic separates C04 runtime execution from C04 benchmark validity. The local OpenFOAM runtime is available and the solver can run the patched motorBike case, but the official mesh path still produces highly skew faces around the motorBike geometry. The force and y+ contracts remain intentionally disabled in this diagnostic profile, so no Cd/Cl, y+, wall-function, or external-aero validation claim is made.

## 后续动作

1. Keep `runtime_layer0_relaxed_skew_wsl_v2412.yaml` as a solver-path isolation profile.
2. Repair the non-diagnostic mesh path by changing geometry/snap/refinement controls until `checkMesh` passes without relaxed diagnostic interpretation.
3. Only after mesh smoke passes, re-enable native `forceCoeffs` and y+ evidence for Cd/Cl and wall-function validation.

## 不得声称

- C04 motorBike mesh smoke has passed.
- C04 external-aero benchmark is validated.
- Cd/Cl, forceCoeffs tail-window, or y+ evidence is available.
- Relaxed-skew solver-path success is equivalent to a production mesh-quality pass.
