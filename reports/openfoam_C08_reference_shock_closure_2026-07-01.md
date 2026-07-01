# OpenFOAM C08 reference shock closure - 2026-07-01

## 范围

本报告记录 C08 reduced-CFL runtime 的 shock reference closure 状态。

- capability: `C08_compressible_shock_capturing_forward_step`
- config: `configs/openfoam/compressible_shock_capturing_forward_step/cfl_reduced.yaml`
- result root: `_results/openfoam/compressible_shock_capturing_forward_step/cfl_reduced`
- solver: `rhoCentralFoam`
- gate: `smoke`

## Reference Source

`cfl_reduced.yaml` 已配置 `shock_reference.reference_policy: accepted_baseline_samples`，其 reference 来自本地 runtime smoke：

- `source_id: openfoam_C08_cfl_reduced_runtime_smoke_2026-07-01`
- `source_type: local_runtime_smoke`
- `shock_position_reference_m: 0.425`
- `pressure_jump_ratio_reference: 7.6237`
- `density_jump_ratio_reference: 3.282`
- `accepted_baseline_samples.status: smoke_reference_only`

该 reference 可以关闭 C08 当前的 smoke 级 shock-reference 缺口，但不能作为外部 benchmark 或 double-v 证据。

## Runtime Evidence

Reduced-CFL runtime 已完成：

- `blockMesh`: returncode `0`
- `checkMesh`: returncode `0`
- `rhoCentralFoam`: returncode `0`
- final time: `4.0`
- max Courant: `0.0949348`
- shock position: `0.425`
- pressure jump ratio: `7.623675555555555`
- density jump ratio: `3.2820011603091723`
- boundary mass imbalance proxy: `0.025242669026375803`
- boundary total-energy imbalance proxy: `0.011272417945887505`

The measured shock position and jump ratios match the configured accepted baseline samples within current smoke tolerances.

## 判定

C08 的 reference shock closure 当前状态是：

- local accepted-baseline smoke reference: closed。
- solver runtime / max-CFL / shock extraction / jump sanity / artifact completeness: passed。
- external benchmark reference: not closed。
- native or face-field flux parity: not closed。
- benchmark promotion: 不允许，保持 `package_skeleton_created`。
- promotion guard: `local_runtime_smoke` + `smoke_reference_only` 不允许通过 promotion-grade shock reference provenance check。

这一区分很重要：C08 已经不是“没有 reference shock target”的状态；它现在有 smoke 级 accepted baseline reference。但该 reference 来源于同一套本地 runtime，不能证明外部准确性，也不能替代 native/face-flux parity。

## 后续判据

若要从 smoke 推进到 benchmark validation，需要至少补齐：

1. 外部或独立 reference shock position / pressure jump / density jump targets。
2. `boundary_flux_owner_cell_proxy` 对 native OpenFOAM flux 或 face-field integration 的 parity。
3. mesh refinement 或 inlet Mach perturbation 下的 shock metric 趋势。
