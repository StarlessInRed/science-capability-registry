# Fluent Source Intake

日期：2026-07-02

## 结论

Fluent 官方材料应按来源角色拆分，而不是按文件夹机械一一对应 PDF。`Fluent_Tutorial_Package` 基本对应 2025 R1 Fluent Tutorial Guide 的 case package；`Fluent_Workbench_Tutorial_Package` 对应 Workbench Tutorial Guide；`ansys_fluid_dynamics_verification_manual.pdf` 当前未发现同名 case package，应作为 reference/benchmark source；`Fluent_tutorial_case` 和 `legacy_2020_r2_unique` 是 legacy/辅助来源。

## 本轮扫描结果

| 来源 | 数量/特征 | 资产角色 |
| --- | --- | --- |
| `Fluent_Tutorial_Package` | 75 个 zip | 官方 tutorial replay 候选 |
| `Fluent_Workbench_Tutorial_Package` | 3 个 zip | Workbench/参数化集成候选 |
| `legacy_2020_r2_unique` | 1 个 zip | 旋转/滑移补充 |
| `Fluent_tutorial_case` | `ch03`-`ch16`、`UserGuide_17.06.pdf`、直接 `.cas/.dat/.msh/.jou` | standalone runtime seed 候选 |
| verification manual | PDF only in current library | validation/reference source |

## 代表性 zip 观察

- `fluent_aero_tutorial.zip` 含 aircraft/capsule/wing mesh 和 reference CSV，可支撑外流气动 C04。
- `vof.zip` 含 `inkjet.msh`，可支撑 VOF/free-surface C05 的 mesh/setup replay。
- `sliding_mesh.zip` 含 `axial_comp.msh` 和 `.msh.h5`，可支撑 C06 moving mesh seed。
- `2d_heat_exchanger_optimizer.zip` 含 `.cas.h5/.dat.h5`，可支撑 C07 heat-transfer replay。
- `workbench_parameter.zip` 含 `.wbpz`，可支撑 C08 Workbench parameter handoff。

## Runtime preflight

用户确认本机有 Fluent 执行环境；多 agent 运行时探测进一步发现本机存在 Ansys 2025 R1/v251 的 Fluent 与 Workbench 可执行文件，但它们不在 PATH。仓库提交的 runtime profile 只记录 `executables_found_by_local_probe_but_not_on_path`、版本族和注入字段，不固化本机盘符路径。后续 runtime smoke 应通过本机环境变量或 ignored machine profile 注入 `FLUENT_EXE`、`RUNWB2_EXE`、`AWP_ROOT251`，再执行最小 C01 batch journal。

## 下一步

1. 先用 `configs/fluent/seed_suite/c01_c08_static_readiness.yaml` 保持 C01-C08 的静态配置闭环。
2. 再实现 C01 standalone Fluent batch smoke 的 source extraction、journal contract 和 metrics parser。
3. 选择 C02 verification manual 中一个几何/reference 同构的简单 case，建立 benchmark gate。
4. 逐步扩展 C03-C08，并用官方 zip replay 对比自生成算例。
