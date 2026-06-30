# OpenFOAM C03 intern task: backward-facing step RANS internal flow

目标：维护并扩展 cfd.openfoam.backward_facing_step_rans_internal_flow 能力。当前已完成本机 OpenFOAM.com v2112 integration benchmark，后续不要把它误称为外部实验验证。

## 当前交付

- run schema: schemas/openfoam_C03_backward_facing_step_rans_internal_flow.schema.json
- package: src/science_capability_registry/openfoam/backward_facing_step_rans_internal_flow/
- configs: configs/openfoam/backward_facing_step_rans_internal_flow/
- report: reports/openfoam_C03_backward_facing_step_rans_internal_flow_benchmark_validation.md

## 后续验收方向

1. 解决本机 OpenFOAM functionObject sha1 IO 错误后，用原生 wallShearStress/yPlus 与 Python proxy 做一致性检查。
2. 引入 Pitz & Daily 或 ERCOFTAC 参考数据，定义再附长度和压力系数误差阈值。
3. 增加 kOmegaSST 作为独立 turbulence-model perturbation，不要混入当前 kEpsilon benchmark 结论。
