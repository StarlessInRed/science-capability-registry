# Gmsh examples_index

本文件登记已经转化或待转化为科学能力资产的 Gmsh 官方文档、tutorial、benchmark 和本地 case 来源。

| ID | 来源 | capability | domain | 资产卡 | benchmark 状态 | evidence scope | next gate | known blockers | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Gmsh reference manual and official `t1.geo` tutorial | parametric geometry and mesh generation | meshing | `software/gmsh/assets/C01_parametric_geometry_mesh_generation.yaml` | benchmark candidate | official documentation and tutorial evidence only | static-readiness schema/config design | 缺少本仓库 run schema、baseline config、Gmsh runtime profile、mesh-quality metrics、下游 solver import smoke | 先定义参数化几何、physical group 和 mesh-quality 的能力边界，不提前提升为已验证能力。 |
