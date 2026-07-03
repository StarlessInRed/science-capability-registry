# COMSOL C01-C06 Cross-Profile Regression Boundary - 2026-07-03

本报告记录 COMSOL C01-C06 的 cross-profile regression 任务边界。当前本机已经具备 MATLAB/COMSOL/LiveLink 路径，但第二机器或第二 runtime profile 的复测证据尚未进入仓库。

## Regression Matrix

| group | local baseline | second profile target | claim if passed |
| --- | --- | --- | --- |
| C01 | `local_livelink_smoke` | another COMSOL host/profile | bridge portability smoke |
| C02 | `local_livelink_model_tree_smoke` | another COMSOL host/profile | API model-tree portability smoke |
| C03-C06 | `local_livelink_heat_rectangle` | another COMSOL host/profile | generated-case portability smoke |
| C03-C06 official replay | `domain_activation_official_replay_smoke` | another COMSOL host/profile | official replay portability smoke |

## Required Evidence

- Same config path and schema path on both profiles.
- Runtime profile recorded through environment/config boundary, not hardcoded paths.
- `metrics.json`, `validation.json`, `manifest.json`, and `validation_report.md` retained under `_results/comsol/...`.
- Stable summary promoted to `reports/` only after the second profile run finishes.

## Current Boundary

This report closes the contract side of the cross-profile task: what must be compared, where evidence lives, and what not to claim. It does not claim cross-profile runtime success yet.
