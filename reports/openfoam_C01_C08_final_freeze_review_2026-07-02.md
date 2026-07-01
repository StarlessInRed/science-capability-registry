# OpenFOAM C01-C08 Final Freeze Review

日期：2026-07-02

## 结论

OpenFOAM 首批 C01-C08 可以在当前阶段冻结并转向其他科学资产。这里的冻结含义是：repo 中已经有能力卡、schema/config/package 或稳定诊断证据，失败和 promotion gap 已进入 failure ledger 或稳定报告；冻结不表示所有能力都完成外部 benchmark 或 double-v。

## 最终状态

| C | 当前冻结结论 | 可保留声明 | 不声明 |
| --- | --- | --- | --- |
| C01 | accepted local integration | lid-driven cavity 本地 integration 可复跑 | 外部中心线 double-v |
| C02 | non-promotional case-freeze | finite-domain diagnostic、solver/artifact/error extraction 可用 | 无界圆柱解析 benchmark |
| C03 | accepted local integration | pitzDaily RANS 本地 integration 可复跑 | 外部 BFS reference、native wall-shear/y+ parity |
| C04 | local case-freeze accepted | strict mesh、simpleFoam、native forceCoeffs、finite yPlus diagnostic | y+ band certification、Cd/Cl reference convergence |
| C05 | local finite-domain case-freeze accepted | OpenFOAM cylinder2D finite-domain Strouhal 证据 | 外部 free-cylinder benchmark |
| C06 | accepted local integration | damBreak VOF short/full-horizon local evidence | 外部 dam-break double-v、sampleSets value parity |
| C07 | local case-freeze accepted | MHR baseline/perturbation 和 native wallHeatFlux field smoke | cpuCabinet validation、steady heat-rate parity |
| C08 | local shock smoke/case-freeze accepted | reduced-CFL shock smoke、local shock reference、face-field flux integration | 外部 shock benchmark、native flux parity |

## 冻结后的恢复入口

恢复 OpenFOAM 时只从这些 promotion gaps 继续，不重新展开 C01-C08：

1. C02 finite-domain corrected reference 或 domain-expanded analytical convergence。
2. C04 wall-normal layer/y+ band closure 和 Cd/Cl convergence/reference。
3. C05 domain/mesh/time-step sensitivity 与 independent frequency extraction。
4. C07 parsed native/reference heat-rate parity 和更长稳态收敛。
5. C08 external/independent shock reference 与可选 native flux parity。
6. C01/C03/C06 double-v reference/value parity。

## 对后续 Fluent/COMSOL 的启发

OpenFOAM 可以暂放，不是因为“CFD 都做完了”，而是因为第一批能力已经把 runtime、postprocess、reference policy、失败分类和 promotion 边界跑通。Fluent 和 COMSOL 应复用这个冻结口径：先完成 C01-C06 的资产化和最小 runtime，再决定哪些值得进入 expensive benchmark 或 double-v。
