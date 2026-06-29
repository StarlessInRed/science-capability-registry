# 任意科学计算网页转能力资产卡提示词

你要把一个科学计算网页转化为 scientific capability card。不要把网页整理成教程，不要要求用户亲自学习软件操作。

## 输入

- `source_url`：网页地址。
- `software`：涉及的软件，例如 Cantera、OpenFOAM、Fluent、COMSOL、Abaqus、Gmsh、ParaView。
- `target_domain`：科学问题域，例如 combustion、cfd、multiphysics、meshing、numerical_solvers。
- `intended_capability`：希望沉淀的 capability 名称。

## 处理原则

- 网页是能力证据，不是学习材料。
- example 是 benchmark，不是教程。
- 所有内容必须面向“实习生可执行、负责人可验收、个人或 MatOS 可集成”。
- 必须抽象求解器、物理模型、网格或离散、边界条件、输入、输出、收敛性、物理正确性和自动验证。
- 如果网页缺少关键科学信息，必须显式列出缺口，不要用泛泛描述补齐。

## 输出格式

输出一个 YAML 能力卡，字段必须包含：

```yaml
asset_id:
software:
source_url:
domain:
capability_name:
problem_type:
physics:
inputs:
outputs:
benchmark:
validation_criteria:
integration_targets:
intern_deliverables:
status: draft
```

## 必须回答的问题

- 这个网页证明了什么科学计算能力？
- 该能力对应的问题类型是什么？
- 物理模型、求解器、网格或离散、边界条件分别是什么？
- 哪些参数应进入输入 schema？
- 哪些结果应进入机器可读输出？
- 哪些官方 example 结果可以作为 benchmark？
- 自动验收应检查哪些数值范围、收敛状态、文件产物和物理趋势？
- 实习生应该交付什么？
- 个人 workflow 或 MatOS 后续应如何接入该 capability？

## 禁止输出

- 不要输出学习教程。
- 不要只摘抄网页段落。
- 不要只说“运行官方示例”。
- 不要把 demo 当 capability。
- 不要省略自动验证和物理正确性检查。
