# OpenFOAM C07 intern task: 共轭传热冷却

## 目标

在已经完成的 OpenFOAM.com v2112 `chtMultiRegionSimpleFoam/multiRegionHeaterRadiation` packaged integration matrix 上，把 C07 从“可执行、可扰动、可抽取 proxy 指标”继续推进到可验证的 CHT benchmark capability。

当前状态仍然不是 `benchmark_validated`。原因是本地证据只有短时 `Time=2` integration matrix，interface heat-flux 仍是 Python patch-face proxy，不是 native heat-flux conservation，也没有外部参考值或 double-v 对比。

## 当前证据

- capability card: `software/openfoam/assets/C07_conjugate_heat_transfer_cooling.yaml`
- runtime profile: `configs/openfoam/runtime_profiles/openfoam_com_v2112_cht.yaml`
- baseline config: `configs/openfoam/conjugate_heat_transfer_cooling/baseline_multi_region_heater_radiation_wsl_v2112.yaml`
- perturbation configs:
  - `configs/openfoam/conjugate_heat_transfer_cooling/perturb_heater_temperature_high_wsl_v2112.yaml`
  - `configs/openfoam/conjugate_heat_transfer_cooling/perturb_airflow_high_wsl_v2112.yaml`
  - `configs/openfoam/conjugate_heat_transfer_cooling/perturb_mesh_refinement_wsl_v2112.yaml`
- integration report: `reports/openfoam_C07_conjugate_heat_transfer_cooling_multiRegionHeaterRadiation_integration_matrix_2026-06-30.md`
- solver: `/opt/OpenFOAM-v2112/platforms/linux64GccDPInt32Opt/bin/chtMultiRegionSimpleFoam`
- tutorial: `/opt/OpenFOAM-v2112/tutorials/heatTransfer/chtMultiRegionSimpleFoam/multiRegionHeaterRadiation`
- regions: fluid `bottomAir`, `topAir`; solid `heater`, `leftSolid`, `rightSolid`

`cpuCabinet` 保留为失败诊断 evidence：低并行数下 `realizableKE` 与 `kEpsilon` 都在 `Time=2` 附近复现 FPE，不再作为默认 packaged baseline。

## 已闭环交付

1. 已建立三类 perturbation configs：heater fixed-temperature 升高、topAir airflow/boundary velocity 变化、blockMesh mesh refinement。
2. 已为 baseline 与三类 perturbation 生成本地 runtime `metrics.json`、`validation.json`、`region_temperature_summary.csv`、`interface_balance_summary.csv`、`patch_heat_flux_proxy_summary.csv`。
3. 已实现 patch-face owner-cell series-resistance heat-flux proxy，并进入 `metrics.json` 与 runtime validation availability check。
4. 已增加 pytest 覆盖：schema matrix configs、runner patching、runtime proxy gate、postprocess proxy extraction。
5. 已更新 capability card、examples index 和 integration report。

## 下一步必须交付

1. 实现 native 或可独立复核的 patch heat-flux extraction。
   - 首选 OpenFOAM native functionObject 或可复现的 field operation。
   - 如果继续使用 Python，需要输出 face area、normal convention、radiative flux inclusion policy、per-interface heat-rate balance，并说明与 native 结果的偏差。
2. 延长 CHT 运行时间或设置稳态收敛判据。
   - 当前 `endTime=2` 只能证明 wiring 与短时非发散。
   - 后续需要记录 residual history、temperature asymptote、heat-rate trend 是否稳定。
3. 建立 double-v 或 reference comparison。
   - 可选择官方 tutorial 预期、独立热阻近似、文献值，或另一个 solver/mesh 的对照。
   - 不能只用截图或单个标量。
4. 增加 airflow 物理指标。
   - 当前 airflow perturbation 证明 U boundary patching 和 solver robustness。
   - 后续应抽取流体区 `U` magnitude、inlet/outlet flow-rate proxy 或 convective heat-transfer response。
5. 补 mesh/decomposition sensitivity。
   - 当前 mesh refinement 只证明 cell count 改变后仍能运行。
   - 后续需要至少两个 mesh levels 或 decomposition variants，并记录关键温度/热率指标的相对差异。

## 验收门槛

- `smoke`: baseline 到达配置终点，五个 region 字段有限，radiation artifacts 与 validation artifacts 均生成。
- `integration`: baseline 加三类 perturbation 均通过，并记录清晰物理趋势。
- `double-v`: native/reference heat-flux、长时收敛和外部对比通过后，才允许考虑 `benchmark_status=benchmark_validated`。

## 下一步验收检查

1. 建立 native 或独立复核的 interface heat-flux metric pipeline。
   - 必须输出 face area、normal convention、radiative flux inclusion policy、per-interface heat-rate balance。
   - 必须给出 heat-flux mismatch tolerance，且比当前 proxy availability check 更严格。
2. 延长 baseline 与 perturbation runs，增加 residual history、temperature asymptote 和 heat-rate trend 稳定性检查。
3. 增加 airflow 物理响应指标，例如 fluid-region `U` magnitude、inlet/outlet flow-rate proxy 或 convective heat-transfer response。
4. 增加 mesh/decomposition sensitivity，至少比较两个 mesh levels 或 decomposition variants 的关键温度/热率相对差异。
5. 在 native/reference heat-flux、长时收敛和 independent comparison 同时通过前，C07 维持 `benchmark_candidate`。

## 风险

- 当前 integration matrix 仍是短时 `Time=2`，不代表稳态收敛。
- 当前 patch heat-flux 是 owner-cell temperature gradient proxy，忽略辐射贡献和湍流热扩散。
- 本机 OpenFOAM.com v2112/WSL functionObject 写出存在 `sha1` IO 风险；当前 baseline 通过清空 `controlDict.functions` 规避。
- `externalCoupledHeater` 带外部耦合接口，不应混入 C07 MHR perturbation matrix。
- `heatExchanger` 在 v2112 中没有 solid region，不能作为固-流 CHT 主基准。
