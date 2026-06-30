# OpenFOAM C04 intern task: motorBike 外流气动 RANS

## 目标

把 OpenFOAM.com v2112 `incompressible/simpleFoam/motorBike` 官方 tutorial 转化为 `cfd.openfoam.external_aero_motorbike_rans_snappy` 能力。该能力必须覆盖 snappyHexMesh 网格质量、RANS 求解、forceCoeffs、`Cd`/`Cl` 和 `y+`，不能只停留在几何展示或 solver smoke。

当前状态为 `benchmark_candidate`。仓库已有 capability card 和 examples index 入口，但还没有 run schema、baseline config、case generator、runtime runner、force/y+ 后处理、metrics 或验证报告。

## 源证据

- solver: `simpleFoam`
- mesh workflow: `blockMesh`、`surfaceFeatureExtract`、`snappyHexMesh`、`checkMesh`
- tutorial: `$FOAM_TUTORIALS/incompressible/simpleFoam/motorBike`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C04_external_aero_motorbike_rans_snappy.yaml`

## 必须交付

1. 建立 config-first run schema，至少暴露 runtime profile、official template source、motorBike 几何源、snappyHexMesh refinement、来流速度、湍流模型、wall functions、force reference area、`y+` 阈值和 mesh quality 阈值。
2. 建立 baseline config，默认使用官方 motorBike tutorial，并把几何、网格、solver、functionObjects 和 validation thresholds 写入配置。
3. 实现 dry-run manifest，列出 mesh workflow、patch roles、field requirements、forceCoeffs 输出、`y+` 输出和 artifact targets。
4. 实现 mesh 阶段 gate，解析 `checkMesh`，至少检查 cell count、patch 完整性、non-orthogonality、skewness、aspect ratio 和 fatal mesh errors。
5. 实现 runtime runner，顺序执行网格生成、mesh 检查、`simpleFoam` 和必要 functionObjects。
6. 实现 `forceCoeffs`、`Cd`/`Cl`、residual 和 `y+` 后处理；如果必须使用 proxy，必须在 metrics 和报告中显式标注。
7. 增加至少一个 refinement 或 inlet-speed perturbation，记录 mesh/runtime 成本和气动力趋势。
8. 增加 pytest gate，覆盖 schema、dry-run manifest、mesh quality、solver log、force/y+ artifact completeness 和 validation thresholds。
9. 生成验证报告，说明当前 tutorial 是否只能作为趋势 benchmark，是否有可信 Cd/Cl reference，以及 wall-function `y+` 是否落在配置范围。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `mesh smoke`: snappyHexMesh 和 checkMesh 通过，mesh quality 指标进入配置阈值。
- `solver smoke`: `simpleFoam` 正常结束，residual 达标或给出明确未达标原因。
- `integration`: `forceCoeffs`、`Cd`/`Cl`、`y+`、mesh quality 和 solver health 同时进入 metrics，并由 validation.json 给出通过/失败结论。

## 风险

- motorBike tutorial 运行成本和磁盘输出较大，runtime evidence 必须写入 `_results/`，不要提交大型结果。
- `Cd`/`Cl` 对 reference area、来流定义、几何尺度和时间/迭代窗口敏感，必须把定义写入 config。
- `y+` 是 wall-function 合理性的必要证据；缺少 `y+` 时不能把 C04 提升为 validated benchmark。
