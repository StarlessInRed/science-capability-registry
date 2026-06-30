# OpenFOAM C06 intern task: dam break VOF free surface

目标：维护并扩展 cfd.openfoam.dam_break_vof_free_surface 能力。当前已完成本机 OpenFOAM.com v2112 short-horizon integration benchmark，后续不要把它误称为实验 dam-break validation。

## 当前交付

- run schema: schemas/openfoam_C06_dam_break_vof_free_surface.schema.json
- package: src/science_capability_registry/openfoam/dam_break_vof_free_surface/
- configs: configs/openfoam/dam_break_vof_free_surface/
- report: reports/openfoam_C06_dam_break_vof_free_surface_benchmark_validation.md

## 后续验收方向

1. 增加 full-horizon endTime=1.0 矩阵，并记录 runtime 成本。
2. 引入 Martin & Moyce 或其它 dam-break 前缘参考数据，定义前缘位置误差阈值。
3. 解决 sampling functionObject 的本机 sha1 IO 错误后，与 Python alpha parser 做一致性检查。
