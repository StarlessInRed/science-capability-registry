# COMSOL C03-C06 Domain Activation Official Replay Smoke - 2026-07-03

本报告记录 `livelink_domain_activation` 官方 Application Library 候选的 MATLAB LiveLink replay smoke。运行输出位于 `_results/comsol/application_library_replay/domain_activation_official_replay_smoke/`。

不提交 `.mph` 或 runtime 产物。

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

- C03: official model open and selection-map mutation are captured.
- C04: Heat Transfer physics and boundary-assignment handoff artifacts are captured.
- C05: official study run completes and dataset manifest is written.
- C06: scalar extraction through `mphglobal` is exported with unit metadata.

## No Claims

- This is one official Application Library replay smoke, not full tutorial parity.
- It does not claim analytical benchmark validation, double-v, or broader multiphysics correctness.
- C03-C06 generated heat-rectangle smoke remains the primary catalog evidence until promotion is reviewed separately.
