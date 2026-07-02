# COMSOL C02 model construction API contract intern task

## 目标

在 C01 bridge 可用后，用 MATLAB/API 构建 COMSOL model tree，并把参数、component、geometry、mesh、study 等关键 tag 写成可验证 contract。

## 交付物

- C02 config/schema/package/tests。
- `model_tree_manifest.json` 和 `construction_manifest.json`。
- 正向和负向 validation。

## 验证标准

- 必须显式声明 model/component/geometry/material/mesh/study tag。
- 缺参数、缺 tag、未知 tag 必须失败。
- model construction 成功不等于 solver run 或 physics validation。
