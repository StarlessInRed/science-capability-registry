# OpenFOAM 能力资产建设 prompt

用途：把 OpenFOAM 网页、官方 tutorial、solver 文档、论文 benchmark 或本地 case 转化为本仓库的科学能力资产，并逐步推进到可运行 package、自动验证和验收报告。

## 可直接复制的指令

请把下面 OpenFOAM 资料转化为 `science-capability-registry` 中的科学能力资产，并按仓库规则逐步推进。

资料：

```text
<URL 或本地 case 路径>
```

目标：

```text
<可选：目标 capability，例如 C01 lid-driven cavity、C03 backward-facing step、C06 dam break；如果不确定，请先判断>
```

要求：

1. 使用 `$openfoam-capability-intake` 判断资料属于哪个 OpenFOAM distribution、version、solver family、domain 和 capability。
2. 先搜索 `software/openfoam/assets/`、`software/openfoam/examples_index.md` 和 `software/openfoam/capability_map.md`，如果已有类似 capability，不要重复新建，优先更新现有资产。
3. 不要把网页整理成教程。网页是 capability evidence，官方 tutorial 是 benchmark candidate，不是让用户手动学习软件操作。
4. 每个 OpenFOAM 案例必须抽象为：
   - 问题类型
   - governing model 或 model class
   - solver 和 OpenFOAM distribution/version
   - geometry、mesh 或 discretization
   - initial conditions
   - boundary conditions
   - numerical schemes、solver tolerance、time controls 和 functionObjects
   - 输入参数 schema
   - 输出字段、标量指标、CSV、图和日志
   - benchmark source
   - validation criteria
   - intern deliverables
   - personal workflow 或 MatOS integration pathway
   - risks and limitations
5. 使用状态字段 `card_status` 和 `benchmark_status`，不要写旧的顶层 `status` 字段。
6. 如果只是官方资料登记，`benchmark_status` 默认是 `benchmark_candidate`；只有 schema、config、package、dry-run、solver metrics、validation report 和 tests 都具备时，才允许提升到 `benchmark_validated`。
7. 如果需要设计可运行能力，使用 `$openfoam-case-contract` 先创建 config-first 的 schema 和 baseline config，明确 `0/`、`constant/`、`system/`、fields、patches、BC、numerics、runtime controls、postprocess targets 和 validation gates。
8. 如果需要实现 package，使用 `$openfoam-runner-postprocess`，要求先支持 `--dry-run`，生成 manifest，再通过显式 backend 执行 mesh、solver、postprocess，并输出 `metrics.json`、CSV、plots、logs 和 validation summary。
9. 如果需要验收或提升状态，使用 `$openfoam-validation-review` 检查 residual、continuity、Courant number、mesh quality、boundedness、y+、forces/probes、conservation、physical trends、failure modes 和 artifact completeness。
10. 所有任务必须面向“实习生可执行、负责人可验收、个人 workflow 或 MatOS 可集成”，不能停留在简单 demo。

## 当前 OpenFOAM 能力地图

优先从 C01、C03、C06 开始，因为它们能覆盖基础不可压流、RANS 内流和多相自由表面三类核心能力。

| Capability | Slug | Solver family | Domain | 第一阶段优先级 |
| --- | --- | --- | --- | --- |
| C01 | `lid_driven_cavity_incompressible_laminar` | incompressible laminar steady/transient | CFD | 是 |
| C02 | `potential_flow_cylinder_analytical_validation` | potential/inviscid flow | CFD | 否 |
| C03 | `backward_facing_step_rans_internal_flow` | incompressible RANS internal flow | CFD | 是 |
| C04 | `external_aero_motorbike_rans_snappy` | external aerodynamics with snappyHexMesh | CFD | 否 |
| C05 | `transient_cylinder_vortex_shedding` | transient incompressible flow | CFD | 否 |
| C06 | `dam_break_vof_free_surface` | multiphase VOF free surface | multiphysics | 是 |
| C07 | `conjugate_heat_transfer_cooling` | conjugate heat transfer | multiphysics | 否 |
| C08 | `compressible_shock_capturing_forward_step` | compressible transient shocks | CFD | 否 |

## 四段建设流程

### 1. Intake：资料到资产卡

输出：

- `software/openfoam/assets/<asset_id>.yaml`
- `software/openfoam/examples_index.md`
- `software/openfoam/capability_map.md`
- `tasks/openfoam_<asset_id>_intern_task.md`

检查：

- 是否明确 OpenFOAM distribution、version、solver、tutorial path 和 source_url。
- 是否说明该资料证明了什么科学计算能力。
- 是否避免把 official tutorial 当教程抄写。

### 2. Case Contract：资产到可执行契约

输出：

- `schemas/openfoam_<asset_id>.schema.json`
- `configs/openfoam/<capability_slug>/<case_id>.yaml`
- dry-run manifest contract

检查：

- 科学选择必须进入 config/schema，不能藏在 CLI flags 或 Python 常量里。
- OpenFOAM case 字典由 config 生成，复制的 tutorial 文件夹不能作为长期 canonical source。
- backend 必须显式选择，例如 `dry_run_only`、`native_linux`、`wsl` 或 `docker`。

### 3. Runner/Postprocess：契约到 package

输出：

- `src/science_capability_registry/openfoam/<capability_slug>/`
- `_results/openfoam/<capability_slug>/<case_id>/manifest.json`
- `_results/openfoam/<capability_slug>/<case_id>/metrics.json`
- logs、CSV、plots、validation summary

检查：

- 先实现并验证 `--dry-run`。
- 不从 process exit code 直接推断科学成功。
- 必须解析 residual、continuity、Courant、mesh quality、field extrema 和 capability-specific metrics。

### 4. Validation Review：package 到验收状态

输出：

- `reports/openfoam_<asset_id>_<case_id>_validation.md`
- pytest 或等价 validation gate evidence
- `benchmark_status` 更新

检查：

- 最小 gate 使用 `static-readiness`、`smoke`、`targeted-regression`、`integration`、`double-v` 或 `full-regression` 中的稳定命名。
- 状态提升至少需要 baseline solver run、`metrics.json`、validation summary、报告和测试证据。
- 如果验证失败，不要放宽阈值掩盖问题；应记录 failure mode，并在具备 package 的情况下使用 `validation_failed`。

## 第一阶段建议任务

从 C01 `lid_driven_cavity_incompressible_laminar` 开始：

1. 登记 OpenFOAM cavity official tutorial 为 benchmark candidate。
2. 创建 C01 capability card、examples index 和 intern task。
3. 设计 schema/config，参数至少包括 Reynolds number、mesh resolution、solver mode、end time 或 steady convergence settings、residual thresholds 和 sampled outputs。
4. 实现 dry-run package，先不要求本机必须安装 OpenFOAM。
5. 在具备 OpenFOAM backend 后运行 baseline 和至少 3 个 perturbation cases。
6. 验收内容包括 residual convergence、centerline velocity profiles、mass conservation、mesh sensitivity 和 Reynolds number 趋势。

## 禁止事项

- 不要让用户亲自学习 OpenFOAM 操作。
- 不要只复制 tutorial case。
- 不要只做“能跑起来”的 demo。
- 不要省略 mesh、boundary conditions、numerics、convergence 和 physical correctness。
- 不要把 solver-native 大体量 runtime output 提交进 Git。
- 不要在没有本地 metrics 和 validation report 的情况下把 benchmark 标成 validated。
