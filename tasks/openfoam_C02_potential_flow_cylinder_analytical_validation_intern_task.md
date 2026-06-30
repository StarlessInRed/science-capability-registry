# OpenFOAM C02 intern task: 圆柱势流解析验证

## 目标

把 OpenFOAM.com v2112 `basic/potentialFoam/cylinder` 官方 tutorial 转化为 `cfd.openfoam.potential_flow_cylinder_analytical_validation` 能力。该能力的核心不是“运行 potentialFoam”，而是用圆柱势流解析解自动验证速度、压力和表面压力系数。

当前状态为 `package_skeleton_created`。仓库已有 capability card、examples index、run schema、baseline/mesh-refined configs、case generator、runtime runner 入口、解析公式单元测试、static-readiness report 和一次本地 `potentialFoam` runtime attempt。该 runtime attempt 中 `blockMesh` 与 `potentialFoam` 均成功，但速度误差和 `Cp` 误差超阈值，因此不能提升状态。

## 源证据

- solver: `potentialFoam`
- tutorial: `$FOAM_TUTORIALS/basic/potentialFoam/cylinder`
- 本地版本证据: OpenFOAM.com v2112
- 资产卡: `software/openfoam/assets/C02_potential_flow_cylinder_analytical_validation.yaml`

## 必须交付

1. 保持现有 config-first schema、baseline config、mesh-refined config 和 dry-run manifest 与 capability card 同步。
2. 通过 capability CLI 运行本地 `potentialFoam` smoke，保存 solver log、field summary、manifest、metrics 和 validation。
3. 完成解析解后处理，输出速度、压力、表面 `Cp` 的对比 CSV，并计算 `L2`、`Linf` 或等价误差指标。
4. 运行 mesh-refined perturbation，验证解析误差随网格加密下降或解释不下降的数值原因。
5. 增加 pytest gate，覆盖 runtime artifact completeness、解析误差和网格趋势。
6. 生成验证报告，说明解析公式、采样位置、误差阈值、当前 benchmark 状态和不能推广到粘性绕流的边界。

## 验收门槛

- `static-readiness`: capability card、schema、baseline config、dry-run manifest 全部通过。
- `smoke`: `potentialFoam` 正常结束，`U` 和 `p` 字段有限，solver log 无 fatal error。
- `analytical double-v`: 表面 `Cp`、速度场或压力场误差进入配置阈值，并能在网格加密时保持合理趋势。

## 风险

- `potentialFoam` 是势流/初始化类求解器，不能被描述成粘性圆柱绕流或涡脱落能力。
- 圆柱解析解通常假设无界不可压缩无旋流；tutorial 边界和有限计算域会带来系统误差，报告中必须说明。
- `Cp` 的参考压力、速度标定和采样点法向需要统一，否则会出现看似数值失败、实际是定义不一致的问题。
