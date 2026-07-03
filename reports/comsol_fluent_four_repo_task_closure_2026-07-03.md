# COMSOL / Fluent / Four-Repo Task Closure - 2026-07-03

本报告把本轮十个任务的完成边界集中记录。它只汇总已经进入仓库的 config、runner、report、evidence，不替代各能力的 primary evidence 或 benchmark promotion。

| # | task | closure |
| --- | --- | --- |
| 1 | COMSOL C03-C06 official replay runner | Added `schemas/comsol_application_library_replay.schema.json`, `configs/comsol/application_library_replay/*.yaml`, and `src/science_capability_registry/comsol/application_library_replay/`. |
| 2 | COMSOL C06 pseudoperiodicity replay | `reports/comsol_C06_pseudoperiodicity_official_replay_export_smoke_2026-07-03.md` records passed finite export smoke. |
| 3 | COMSOL official replay artifact contract | Replay schema/config require source, selection, physics, boundary, solver, dataset, export, probes, units, metrics, validation, report, and manifest artifacts. |
| 4 | COMSOL C05-C06 analytical heat benchmark | `reports/comsol_C05_C06_analytical_heat_benchmark_policy_2026-07-03.md` defines promotion policy and candidate order. |
| 5 | COMSOL C01-C06 cross-profile regression | `reports/comsol_C01_C06_cross_profile_regression_2026-07-03.md` defines matrix and evidence requirements; second profile is still pending. |
| 6 | COMSOL failure ledger | `reports/comsol_failure_ledger.yaml` records official replay, analytical benchmark, and cross-profile gaps. |
| 7 | Fluent official tutorial source map | Existing source map in `software/fluent/examples_index.md` remains active; current closure points to tutorial, Workbench, verification manual, and legacy sources. |
| 8 | Fluent C01-C08 capability route | `software/fluent/capability_map.md` is refreshed for C02/C03 runtime package state. |
| 9 | Fluent C02/C03 runtime package | `reports/fluent_C02_C03_runtime_package_closure_2026-07-03.md` records C02 pressure-sampling and C03 three-level runtime trend boundaries. |
| 10 | Four-repo route | `reports/four_repo_consumption_boundary_2026-07-03.md` records SCR export tuple and consumer boundaries for gateway, workflow registry, and Sci_AI_OS. |

## Runtime Outcomes

- COMSOL `domain_activation` official replay smoke passed.
- COMSOL `pseudoperiodicity` official replay export smoke passed.
- Fluent C02/C03 runtime evidence is reused from the existing 2026-07-02 runtime closure; no new Fluent runtime was launched in this pass.

## Status Boundary

- COMSOL C03-C06 keep generated heat-rectangle smoke as primary catalog evidence until promotion review.
- Fluent C02/C03 remain smoke/package evidence, not benchmark validation.
- Cross-repo work remains a consumption boundary report; no other repository was edited.
