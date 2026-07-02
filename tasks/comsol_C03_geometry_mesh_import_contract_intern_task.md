# COMSOL C03 geometry mesh import contract intern task

## 目标

验证 MATLAB 驱动 COMSOL 的 geometry、mesh、import 和 selection map 能被稳定构建、记录和检查。

## 交付物

- geometry/mesh config/schema/package。
- `geometry_manifest.json`、`mesh_manifest.json`、`selection_map.json`。
- 缺失 selection、重命名 selection、维度不匹配的负向测试。

## 验证标准

- 所有 solver-facing boundary role 必须来自显式 selection map。
- CAD/import 成功不等于物理求解成功。
- 大型 CAD 不进入 Git；只允许小 fixture 或生成式几何。
