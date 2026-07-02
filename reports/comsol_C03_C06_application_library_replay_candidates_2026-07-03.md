# COMSOL C03-C06 Application Library Replay Candidates - 2026-07-03

本报告记录 C03-C06 从 generated heat-rectangle smoke 进入 official Application Library replay 前的候选选择。它是 source/candidate evidence，不是 runtime replay evidence。

## 结论

首选 replay 线是 `LiveLink_for_MATLAB/Tutorials/domain_activation_llmatlab.m` 与配套 `.mph`。该官方脚本会打开模型、更新 domain selection、运行 study、创建 result dataset/plot，并用 `mphglobal` 提取时间，因此覆盖 C03 selection、C04 assignment mutation、C05 study run、C06 scalar extraction 的最短闭环。

第二 replay 线是 `LiveLink_for_MATLAB/Tutorials/pseudoperiodicity_llmatlab.m` 与配套 `.mph`。该脚本循环求解、用上一段 outlet 温度更新 inlet 插值文件，并通过 `mphinterp` / `mpheval` 导出温度数据，适合强化 C06 的下游表格、finite value 与单位交接验证。

Heat Transfer Module 的 `thin_plate.mph`、`cylinder_conduction.mph`、`localized_heat_source.mph`、`semi_infinite_wall.mph` 保留为物理更纯的二线候选。它们适合后续从 official `.mph` replay 转向热传导 benchmark / analytical comparison，但本轮没有打开二进制模型检查内部 tag。

## Durable Config

- `configs/comsol/application_library_replay_candidates/c03_c06_official_candidates.yaml`

该 config 只记录相对 Application Library path，并要求运行时通过 `COMSOL_APPLICATION_LIBRARY_ROOT` 注入根路径；仓库不提交本机绝对路径、`.mph` 文件或 runtime 结果。

## Candidate Mapping

| candidate | priority | C03 | C04 | C05 | C06 |
| --- | --- | --- | --- | --- | --- |
| `livelink_domain_activation` | 1 | official model open and selection mutation | heat-transfer physics and initial/selection update | repeated `study('std1').run` | `mphglobal` scalar extraction and dataset metadata |
| `livelink_pseudoperiodicity` | 2 | boundary/dataset metadata | inlet temperature reassignment and interpolation input | repeated study loop | `mphinterp` / `mpheval` table export |
| `heat_thin_plate_verification` | 3 | small official geometry/model | heat-transfer assignment | solve-ready verification model | temperature/result extraction candidate |
| `heat_cylinder_conduction_tutorial` | 4 | axisymmetric conduction model | conduction BC/material assignment | stationary solver candidate | field/probe export candidate |
| `heat_localized_heat_source_verification` | 5 | disk heat-source model | localized source assignment | solver candidate | local/global temperature extraction |
| `heat_semi_infinite_wall_verification` | 6 | official model with companion files | heat/moisture material and input data | solver candidate | tabular input/output and units candidate |

## No Claims

- No official `.mph` replay has run in this evidence.
- No COMSOL solver, license, server, working-directory, or feature-tag behavior is validated here.
- No numerical parity, analytical benchmark, double-v, broader multiphysics correctness, or benchmark validation is claimed.
- C03-C06 remain `package_skeleton_created`, with `smoke` gate based on generated heat-rectangle runtime evidence.

## Next Runtime Gate

Implement an `official-replay-smoke` runner using `livelink_domain_activation` first. The runner should resolve `COMSOL_APPLICATION_LIBRARY_ROOT`, execute the official MATLAB script in an isolated output directory, capture selection/assignment/solver/export artifacts, and preserve current generated heat-rectangle evidence as the primary smoke baseline until official replay passes.
