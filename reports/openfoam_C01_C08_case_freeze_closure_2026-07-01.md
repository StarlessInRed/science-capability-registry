# OpenFOAM C01-C08 Case-Freeze Closure

日期：2026-07-01

## 当前阶段口径

本轮按用户确认的口径收敛：`double-v` 不是当前首批 OpenFOAM 工作的关键阻塞项。OpenFOAM C01-C08 可以在本地 case-freeze 范围内结束，然后转向其他科学资产方向。

case-freeze 的含义是：

- 有 repo-stable capability card、schema/config、runner/postprocess 或验证逻辑。
- 有可复验的本地 runtime 或明确的非推广性诊断证据。
- 失败被分类，解决路径或不声称边界已写入资产和 failure ledger。
- 外部 reference、double-v、长时稳态、mesh/time independence 不再阻塞当前阶段，但保留为后续增强。

## C01-C08 状态

| C | 当前结论 | 不声称边界 |
|---|---|---|
| C01 | `benchmark_validated`，本地 integration 和 v2412 replay 已有证据。 | 外部 Ghia-style centerline double-v。 |
| C02 | `benchmark_candidate`，finite-domain diagnostic case-freeze 非推广性闭环。 | 无界圆柱 analytical benchmark、表面 Cp validation。 |
| C03 | `benchmark_validated`，本地 pitzDaily RANS integration 和 v2412 replay 已有证据。 | 外部 BFS RANS reference、native wall-shear/y+ parity。 |
| C04 | `benchmark_validated` for local case-freeze，strict mesh、solver、native forceCoeffs、finite native yPlus diagnostic 通过。 | wall-function y+ band、外部 Cd/Cl reference、mesh-independent aero convergence。 |
| C05 | `benchmark_validated` for local case-freeze，finite-domain cylinder2D native forceCoeffs FFT `St≈0.14` 通过 `[0.13,0.15]`。 | 外部 free-cylinder `[0.16,0.24]` validation、domain/mesh/time independence。 |
| C06 | `benchmark_validated`，本地 damBreak integration、v2412 sampling/full-horizon evidence 已有证据。 | 外部 dam-break reference、native sampleSets value parity。 |
| C07 | `benchmark_validated` for local case-freeze，MHR baseline+perturbation matrix 和 v2412 native wallHeatFlux field smoke 通过。 | cpuCabinet validation、steady heat-flux conservation、native/reference heat-rate parity。 |
| C08 | `benchmark_validated` for local case-freeze，reduced-CFL shock smoke、local shock reference、face-field flux integration 通过。 | 外部 shock benchmark、native `rhoPhi/phi` flux parity、mesh/Mach independence。 |

## 后续路线

OpenFOAM 当前可以暂停。若未来回到 OpenFOAM，优先做的是 P2 增强：

1. C02 finite-domain corrected reference or domain-expanded analytical convergence。
2. C04 wall-normal layer tuning and Cd/Cl reference convergence。
3. C05 external free-cylinder domain/mesh/time-step sensitivity。
4. C07 parsed native or independent two-sided heat-rate parity plus longer steady convergence。
5. C08 external/independent shock reference and optional native flux parity。
6. C01/C03/C06 double-v reference/value parity。

这些工作是增强路线，不是当前转向前的阻塞项。
