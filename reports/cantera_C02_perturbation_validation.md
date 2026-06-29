# Cantera C02 扰动案例验收报告

## 目的

本报告记录 `C02_freely_propagating_premixed_flame` 在三个参数扰动下的自动验收结果和物理趋势。扰动案例用于验证该 capability 不是固定 demo，而是可参数化、可复现、可解释的层流预混火焰速度计算能力。

## Baseline

- Config: `configs/cantera/c02_freely_propagating_premixed_flame/baseline.yaml`
- Reactants: `H2:1.1, O2:1, AR:5`
- Unburned temperature: `300.0` K
- Result: `passed`

| Mode | Flame speed m/s | Peak temperature K | Grid points |
| --- | ---: | ---: | ---: |
| `mixture_averaged` | 0.7187425088779462 | 1857.2046351004196 | 137 |
| `mixture_averaged_soret` | 0.6382291131982496 | 1853.616357090476 | 143 |
| `multicomponent` | 0.7407122243874777 | 1867.6594984562525 | 143 |
| `multicomponent_soret` | 0.6530703202267301 | 1854.7226272117396 | 143 |

## Case 1: 未燃气升温

- Config: `configs/cantera/c02_freely_propagating_premixed_flame/perturbation_temperature_high.yaml`
- Change: `unburned_temperature_k` 从 `300.0` K 提高到 `350.0` K
- Result: `passed`

| Mode | Flame speed m/s | Peak temperature K | Grid points |
| --- | ---: | ---: | ---: |
| `mixture_averaged` | 1.025110894210678 | 1907.7495003174452 | 137 |
| `mixture_averaged_soret` | 0.8911924699040243 | 1893.6930519060777 | 140 |
| `multicomponent` | 1.0344107621012482 | 1911.068001391755 | 141 |
| `multicomponent_soret` | 0.907143556700158 | 1894.8431748598794 | 141 |

趋势解释：未燃气温度升高后，所有 transport mode 的 flame speed 均显著提高，峰值温度也上升。该趋势符合预混火焰中入口温度提高会增强反应速率、缩短化学时间尺度并提高层流火焰速度的物理预期。

## Case 2: 氢气配比提高

- Config: `configs/cantera/c02_freely_propagating_premixed_flame/perturbation_hydrogen_enriched.yaml`
- Change: `reactants` 从 `H2:1.1, O2:1, AR:5` 改为 `H2:1.4, O2:1, AR:5`
- Result: `passed`

| Mode | Flame speed m/s | Peak temperature K | Grid points |
| --- | ---: | ---: | ---: |
| `mixture_averaged` | 1.358464704917973 | 2159.8127881546616 | 132 |
| `mixture_averaged_soret` | 1.188620547659569 | 2145.9091354476836 | 135 |
| `multicomponent` | 1.3559772875435057 | 2162.0327648281336 | 135 |
| `multicomponent_soret` | 1.197733958871626 | 2146.8444964856235 | 135 |

趋势解释：官方 baseline 是强稀释且偏稀的氢气/氧气/氩气预混物。提高氢气比例后，混合物反应性增强，flame speed、峰值温度和最大热释放率都明显上升。该趋势符合从极稀氢气混合物向更高反应性配比移动时火焰传播能力增强的预期。

## Case 3: 无 Soret transport 对照

- Config: `configs/cantera/c02_freely_propagating_premixed_flame/perturbation_no_soret_transport_compare.yaml`
- Change: 只运行 `mixture_averaged` 与 `multicomponent`，两者均关闭 Soret diffusion
- Result: `passed`

| Mode | Flame speed m/s | Peak temperature K | Grid points |
| --- | ---: | ---: | ---: |
| `mixture_averaged` | 0.7187425088779462 | 1857.2046351004196 | 137 |
| `multicomponent` | 0.721904227013925 | 1855.9556434291562 | 137 |

趋势解释：关闭 Soret diffusion 后，mixture-averaged 与 multicomponent 的 flame speed 接近，multicomponent 略高。与 baseline 中启用 Soret 的结果相比，Soret diffusion 会降低该氢气火焰的 flame speed，说明轻组分热扩散效应对氢气预混火焰速度有可观影响。

## 自动验收结论

- 三个扰动 case 均通过 schema 校验。
- 三个扰动 case 的实际 Cantera 求解均通过自动验收。
- 所有运行均输出 CSV、图、日志、`metrics.json` 和 `validation_report.md`。
- `_results/` 中的运行产物不进入 Git；本报告只沉淀可审计的关键 metrics 和物理趋势。

## 风险与后续

- 本批扰动仍局限于 `h2o2.yaml` 和一维自由传播火焰。后续如扩展到甲烷/空气或压力扫描，应新建独立 benchmark case，而不是把不同燃料体系混入同一个 baseline。
- 当前 validation 使用宽参考范围，适合能力级验收；若要做科研级回归测试，应增加 per-case reference tolerance。
