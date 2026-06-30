# OpenFOAM C04 intern task: motorBike 外流气动 RANS

## 目标

把 OpenFOAM.com v2112 `incompressible/simpleFoam/motorBike` 官方 tutorial 转化为 `cfd.openfoam.external_aero_motorbike_rans_snappy` 能力。该能力必须覆盖 snappyHexMesh 网格质量、RANS 求解、forceCoeffs、`Cd`/`Cl` 和 `y+`，不能只停留在几何展示或 solver smoke。

当前状态为 `package_skeleton_created`。仓库已有 capability card、examples index、run schema、baseline/inlet-speed configs、case generator、runtime runner 入口、dry-run manifest、motorBike 几何准备、forceCoeffs contract、`y+` contract 和 static-readiness report；尚未完成 snappyHexMesh/checkMesh/simpleFoam runtime metrics、native forceCoeffs/`y+` evidence、Cd/Cl tail-window 统计和 integration validation。

## 源证据

- solver: `simpleFoam`
- mesh workflow: `blockMesh`、`surfaceFeatureExtract`、`snappyHexMesh`、`checkMesh`
- tutorial: `$FOAM_TUTORIALS/incompressible/simpleFoam/motorBike`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C04_external_aero_motorbike_rans_snappy.yaml`

## 必须交付

1. 保持现有 config-first schema、baseline config、inlet-speed perturbation 和 dry-run manifest 与 capability card 同步。
2. 通过 capability CLI 运行 mesh smoke，解析 `checkMesh`，至少检查 cell count、patch 完整性、non-orthogonality、skewness、aspect ratio 和 fatal mesh errors。
3. 运行 `simpleFoam` 和必要 functionObjects，保存 solver log、mesh log、forceCoeffs 和 `y+` artifacts。
4. 实现或补强 `forceCoeffs`、`Cd`/`Cl`、residual 和 `y+` 后处理；如果必须使用 proxy，必须在 metrics 和报告中显式标注。
5. 使用 inlet-speed perturbation 或 refinement perturbation 记录 mesh/runtime 成本和气动力趋势。
6. 增加 pytest gate，覆盖 mesh quality、solver log、force/y+ artifact completeness 和 validation thresholds。
7. 生成验证报告，说明当前 tutorial 是否只能作为趋势 benchmark，是否有可信 Cd/Cl reference，以及 wall-function `y+` 是否落在配置范围。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `mesh smoke`: snappyHexMesh 和 checkMesh 通过，mesh quality 指标进入配置阈值。
- `solver smoke`: `simpleFoam` 正常结束，residual 达标或给出明确未达标原因。
- `integration`: `forceCoeffs`、`Cd`/`Cl`、`y+`、mesh quality 和 solver health 同时进入 metrics，并由 validation.json 给出通过/失败结论。

## 风险

- motorBike tutorial 运行成本和磁盘输出较大，runtime evidence 必须写入 `_results/`，不要提交大型结果。
- `Cd`/`Cl` 对 reference area、来流定义、几何尺度和时间/迭代窗口敏感，必须把定义写入 config。
- `y+` 是 wall-function 合理性的必要证据；缺少 `y+` 时不能把 C04 提升为 validated benchmark。
