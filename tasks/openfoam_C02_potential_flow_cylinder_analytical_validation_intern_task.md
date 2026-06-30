# OpenFOAM C02 intern task: 圆柱势流解析验证

## 目标

把 OpenFOAM.com v2112 `basic/potentialFoam/cylinder` 官方 tutorial 转化为 `cfd.openfoam.potential_flow_cylinder_analytical_validation` 能力。该能力的核心不是“运行 potentialFoam”，而是用圆柱势流解析解自动验证速度、压力和表面压力系数。

当前状态为 `benchmark_candidate`。仓库已有 capability card 和 examples index 入口，但还没有 run schema、baseline config、case generator、runtime runner、后处理、metrics 或验证报告。

## 源证据

- solver: `potentialFoam`
- tutorial: `$FOAM_TUTORIALS/basic/potentialFoam/cylinder`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C02_potential_flow_cylinder_analytical_validation.yaml`

## 必须交付

1. 建立 config-first run schema，至少暴露 runtime profile、官方 template source、圆柱半径/直径、来流速度、密度、网格分辨率、采样位置和误差阈值。
2. 建立 baseline config，默认指向 OpenFOAM.com v2112 `potentialFoam/cylinder` tutorial。
3. 实现 dry-run manifest，明确 case source、mesh、patch roles、field requirements、postprocess targets 和 validation thresholds。
4. 实现 runtime runner，能够复制或生成 case，执行 `potentialFoam`，保存 solver log、field summary 和 manifest。
5. 实现解析解后处理，输出速度、压力、表面 `Cp` 的对比 CSV，并计算 `L2`、`Linf` 或等价误差指标。
6. 增加至少一个网格加密 perturbation，验证解析误差随网格加密下降或解释不下降的数值原因。
7. 增加 pytest gate，覆盖 schema、dry-run manifest、runtime artifact completeness、解析误差和网格趋势。
8. 生成验证报告，说明解析公式、采样位置、误差阈值、当前 benchmark 状态和不能推广到粘性绕流的边界。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `smoke`: `potentialFoam` 正常结束，`U` 和 `p` 字段有限，solver log 无 fatal error。
- `analytical double-v`: 表面 `Cp`、速度场或压力场误差进入配置阈值，并能在网格加密时保持合理趋势。

## 风险

- `potentialFoam` 是势流/初始化类求解器，不能被描述成粘性圆柱绕流或涡脱落能力。
- 圆柱解析解通常假设无界不可压缩无旋流；tutorial 边界和有限计算域会带来系统误差，报告中必须说明。
- `Cp` 的参考压力、速度标定和采样点法向需要统一，否则会出现看似数值失败、实际是定义不一致的问题。
