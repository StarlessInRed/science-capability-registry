# COMSOL C06 result extraction postprocess validation intern task

## 目标

通过 MATLAB 从 COMSOL 结果中导出 canonical probes、tables、units 和 manifests，让 downstream Python/registry/agent workflow 可以消费。

## 交付物

- export config/schema/package。
- `export_manifest.json`、`probes.csv`、`units.json`、`metrics.json`、`validation.json`。
- Python 侧读取测试。

## 验证标准

- 每个导出量必须有 expression、unit、location/dataset 和物理含义。
- 验证必须拒绝 NaN-only、缺 unit、行列数不匹配。
- result export 必须独立于 solver success 和 benchmark correctness。
