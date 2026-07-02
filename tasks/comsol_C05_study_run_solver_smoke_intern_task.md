# COMSOL C05 study run solver smoke intern task

## 目标

在 C01-C04 稳定后，运行一个完整 MATLAB-driven COMSOL study，验证 solver status、result dataset 和最小结果状态。

## 交付物

- study-run config/schema/package。
- `solver_manifest.json`、`metrics.json`、`validation.json`、`validation_report.md`。
- timeout、convergence-status 和 missing dataset 的负向测试。

## 验证标准

- study 必须达到配置的 completion status。
- 必须产生 expected result dataset。
- solver failure 必须和 model-construction/postprocess failure 分开。
- solver success 不等于 analytical benchmark validation。
