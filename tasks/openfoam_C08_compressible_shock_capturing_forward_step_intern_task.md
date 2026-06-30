# OpenFOAM C08 intern task: 前台阶可压缩激波捕捉

## 目标

把 OpenFOAM.com v2112 `compressible/rhoCentralFoam/forwardStep` 官方 tutorial 转化为 `cfd.openfoam.compressible_shock_capturing_forward_step` 能力。该能力必须验证激波位置、压力/密度跳跃、CFL 和守恒趋势，不能只证明 `rhoCentralFoam` 能生成场文件。

当前状态为 `package_skeleton_created`。仓库已有 capability card、examples index、run schema、baseline/reduced-CFL configs、case generator、runtime runner 入口、dry-run manifest、shock metric 单元测试、static-readiness report 和一次本地 `rhoCentralFoam` runtime attempt。该 runtime attempt 能到达 `Time=4` 且字段有限，但 max Courant、shock sampling、conservation 和 reference jump gate 未通过，因此不能提升状态。

## 源证据

- solver: `rhoCentralFoam`
- tutorial: `$FOAM_TUTORIALS/compressible/rhoCentralFoam/forwardStep`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C08_compressible_shock_capturing_forward_step.yaml`

## 必须交付

1. 保持现有 config-first schema、baseline config、reduced-CFL perturbation 和 dry-run manifest 与 capability card 同步。
2. 通过 capability CLI 执行本地 `rhoCentralFoam` smoke，保存 solver log、Courant history、field extrema、manifest 和 artifact index。
3. 实现 shock 后处理，从配置采样线或等价场切片中提取激波位置、压力跳跃和密度跳跃。
4. 实现守恒检查，至少报告质量守恒误差和可解释的能量 proxy；不能定义清楚时必须保持 `package_skeleton_created` 或更低。
5. 运行 reduced-CFL perturbation，记录激波位置和跳跃量的敏感性。
6. 增加 pytest gate，覆盖 runtime artifact completeness、CFL gate、field boundedness、shock metric 和 conservation metric。
7. 生成验证报告，说明 shock reference、数值耗散、阈值来源和当前 benchmark 状态。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `shock smoke`: `rhoCentralFoam` 正常结束，最大 CFL 未超过配置阈值，`p`、`rho`、`T`、`U` 字段有限且无非物理负值。
- `integration`: shock position、pressure/density jump、CFL history 和 conservation summary 同时进入 metrics，并由 validation.json 给出通过/失败结论。
- `double-v`: shock 位置和跳跃量与配置 reference 或独立计算进入阈值后，才允许考虑 `benchmark_validated`。

## 风险

- 激波捕捉结果对网格、CFL、数值格式和采样线位置敏感，报告必须记录这些配置。
- forwardStep tutorial 可能更适合作为 solver-health benchmark；若缺少可靠 reference，只能先做趋势验证。
- 可压缩守恒指标需要清楚定义控制体、通量和时间窗口，不能用未解释的单个残差替代守恒验证。
