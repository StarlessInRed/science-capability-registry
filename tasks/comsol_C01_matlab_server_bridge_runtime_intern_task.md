# COMSOL C01 MATLAB server bridge runtime intern task

## 目标

把 MATLAB 到 COMSOL 的最小 bridge 做成可复用 capability：环境预检、启动或连接 COMSOL、创建或打开最小模型、运行最小 study、抽取一个有限标量。

## 交付物

- `configs/comsol/matlab_server_bridge_runtime/<case_id>.yaml`
- `schemas/comsol_C01_matlab_server_bridge_runtime.schema.json`
- `src/science_capability_registry/comsol/matlab_server_bridge_runtime/`
- `_results/comsol/matlab_server_bridge_runtime/<case_id>/`

## 验证标准

- 环境变量 `MATLAB_EXE`、`COMSOL_BIN`、`COMSOL_MLI_DIR` 通过预检。
- 运行成功时必须生成 `runtime_manifest.json`、`metrics.json`、`validation.json`、`validation_report.md`。
- 缺少 MATLAB、COMSOL 或 LiveLink API 时必须归类为 runtime-profile failure。
- 不允许把单次 bridge 成功声明为物理 benchmark validation。

## 禁止声明

- 不声明 C02-C06 已完成。
- 不提交本机绝对安装路径。
- 不提交大型 `.mph` 或运行结果文件。
