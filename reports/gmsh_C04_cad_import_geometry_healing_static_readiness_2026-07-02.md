# Gmsh C04 CAD Import Geometry Healing Static Readiness

## 结论

Gmsh C04 已完成 static-readiness 闭环：schema、baseline config、package entrypoint、dry-run CAD import manifest、entity map、healing report、meshability summary、negative validation、catalog dispatch 和 evidence index 均已建立。

本报告不声称真实 OpenCASCADE import 已执行，也不声称 CAD 已成功 mesh。C04 当前证明的是：CAD source provenance、format、unit、import tolerance、healing operations、entity-map expectations、critical-face physical group rebinding 和 meshability thresholds 可以被结构化配置声明，并自动拒绝明显错误。

## 本轮交付

- `schemas/gmsh_C04_cad_import_geometry_healing.schema.json`
- `configs/gmsh/cad_import_geometry_healing/baseline.yaml`
- `src/science_capability_registry/gmsh/cad_import_geometry_healing/`
- `tests/test_gmsh_c04_schema.py`
- `tests/test_gmsh_c04_runner.py`
- `tests/test_gmsh_c04_validation.py`
- `configs/registry/capability_catalog.json` 中的 `meshing.gmsh.cad_import_geometry_healing`

## 验证范围

- baseline config 必须通过 C04 JSON Schema。
- runner dry-run 必须写出 `cad_import_manifest.json`、`entity_map.json`、`healing_report.json`、`meshability_summary.json`、`manifest.json`、`metrics.json`、`validation.json` 和 `validation_report.md`。
- 至少一个 healing operation 必须 enabled，并且必须来自 config。
- imported entity 和 surface count 必须可追踪。
- critical faces 必须绑定 required physical groups。
- unassigned entity、duplicate 或 sliver entity 必须在阈值内。
- validation report 必须明确区分 CAD healing correctness 和 mesh generation success。

## 当前状态

- `card_status`: `review`
- `benchmark_status`: `package_skeleton_created`
- `dispatch_status`: `static_ready`
- `current_gate`: `static-readiness`

## 未验证风险

- 尚未执行真实 OpenCASCADE CAD import。
- 尚未从真实 CAD runtime artifact 中解析 imported/modified/deleted/new entity tag。
- 尚未执行 CAD-to-mesh smoke。

## 下一步

把 generated-smoke contract 接到真实 OpenCASCADE runtime，优先使用可生成的小型 CAD case，继续避免大型 CAD fixture 和生成 mesh 进入 Git。
