# COMSOL C06 Pseudoperiodicity Official Replay Export Smoke - 2026-07-03

本报告记录 `livelink_pseudoperiodicity` 官方 Application Library 候选的 C06-oriented export smoke。运行输出位于 `_results/comsol/application_library_replay/pseudoperiodicity_official_replay_export_smoke/`。

## Result

| metric | value |
| --- | --- |
| runtime status | `matlab_livelink_application_library_replay_passed` |
| MATLAB return code | `0` |
| source files existing | `2 / 2` |
| required env configured | `4 / 4` |
| selection role count | `1` |
| physics created | `true` |
| missing boundary assignment count | `0` |
| solver completed | `true` |
| dataset count | `1` |
| exported probe count | `1` |
| finite value fraction | `1.0` |
| missing unit count | `0` |

## Covered Contracts

- C03/C04/C05 receive official replay smoke coverage for source open, assignment presence, and study execution.
- C06 receives stronger table/export coverage through an official tutorial using temperature extraction semantics.

## No Claims

- This is a table/finite-value export smoke, not a full pseudoperiodic tutorial parity run.
- It does not claim heat-transfer benchmark validation, double-v, or broad multiphysics correctness.
- It does not replace C06 generated heat-rectangle primary evidence without a separate promotion review.
