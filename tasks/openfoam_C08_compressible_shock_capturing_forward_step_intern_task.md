# OpenFOAM C08 intern task: 前台阶可压缩激波捕捉

## 目标

把 OpenFOAM.com v2112 `compressible/rhoCentralFoam/forwardStep` 官方 tutorial 转化为 `cfd.openfoam.compressible_shock_capturing_forward_step` 能力。该能力必须验证激波位置、压力/密度跳跃、CFL 和守恒趋势，不能只证明 `rhoCentralFoam` 能生成场文件。

当前状态为 `benchmark_candidate`。仓库已有 capability card 和 examples index 入口，但还没有 run schema、baseline config、case generator、runtime runner、shock 后处理、metrics 或验证报告。

## 源证据

- solver: `rhoCentralFoam`
- tutorial: `$FOAM_TUTORIALS/compressible/rhoCentralFoam/forwardStep`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C08_compressible_shock_capturing_forward_step.yaml`

## 必须交付

1. 建立 config-first run schema，至少暴露 runtime profile、official template source、前台阶几何、来流 Mach 或完整热力状态、thermophysical properties、time controls、CFL 阈值、shock sampling lines 和守恒阈值。
2. 建立 baseline config，默认使用官方 `rhoCentralFoam/forwardStep` tutorial。
3. 实现 dry-run manifest，明确字段 `U`、`p`、`T`、`rho`、时间控制、thermophysical model、shock sample targets 和 validation thresholds。
4. 实现 runtime runner，执行 `rhoCentralFoam`，保存 solver log、Courant history、field extrema、manifest 和 artifact index。
5. 实现 shock 后处理，从配置采样线或等价场切片中提取激波位置、压力跳跃和密度跳跃。
6. 实现守恒检查，至少报告质量守恒误差和可解释的能量 proxy；不能定义清楚时必须保持 benchmark_candidate。
7. 增加至少一个 CFL 或网格 perturbation，记录激波位置和跳跃量的敏感性。
8. 增加 pytest gate，覆盖 schema、dry-run manifest、runtime artifact completeness、CFL gate、field boundedness、shock metric 和 conservation metric。
9. 生成验证报告，说明 shock reference、数值耗散、阈值来源和当前 benchmark 状态。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `shock smoke`: `rhoCentralFoam` 正常结束，最大 CFL 未超过配置阈值，`p`、`rho`、`T`、`U` 字段有限且无非物理负值。
- `integration`: shock position、pressure/density jump、CFL history 和 conservation summary 同时进入 metrics，并由 validation.json 给出通过/失败结论。
- `double-v`: shock 位置和跳跃量与配置 reference 或独立计算进入阈值后，才允许考虑 `benchmark_validated`。

## 风险

- 激波捕捉结果对网格、CFL、数值格式和采样线位置敏感，报告必须记录这些配置。
- forwardStep tutorial 可能更适合作为 solver-health benchmark；若缺少可靠 reference，只能先做趋势验证。
- 可压缩守恒指标需要清楚定义控制体、通量和时间窗口，不能用未解释的单个残差替代守恒验证。
