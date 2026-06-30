# Gmsh examples_index

本文件登记已经转化或待转化为科学能力资产的 Gmsh 官方文档、tutorial、benchmark 和本地 case 来源。

| ID | 来源 | capability | domain | 资产卡 | benchmark 状态 | evidence scope | next gate | known blockers | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Gmsh reference manual and official `t1.geo` tutorial | parametric geometry and mesh generation | meshing | `software/gmsh/assets/C01_parametric_geometry_mesh_generation.yaml` | package skeleton created | official documentation plus local schema/config/package dry-run contract | smoke runtime and downstream import | 缺少下游 solver import smoke；mesh-quality 指标仍是基础 triangle proxy | 已建立 `.geo` 生成、Python API runtime、mesh summary 和 validation contract；不提前提升为已验证能力。 |
