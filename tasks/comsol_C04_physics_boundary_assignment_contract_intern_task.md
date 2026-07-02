# COMSOL C04 physics boundary assignment contract intern task

## 目标

把 physics interface、material、boundary condition 和 initial condition assignment 从 model construction 中拆出来，单独验证 completeness 和 unit policy。

## 交付物

- physics/boundary assignment config/schema/package。
- `physics_assignment_manifest.json` 和 `boundary_assignment_manifest.json`。
- 缺 material、缺 BC、缺 unit、未知 physics tag 的负向测试。

## 验证标准

- 每个 solver-facing boundary role 必须有 assignment 或显式 out-of-scope reason。
- validation 必须拒绝缺 unit、缺 material assignment、未知 physics tag。
- assignment completeness 不等于 solver convergence。
