# Cantera C02 自由传播预混火焰验收报告

## Case

- Capability: `combustion.cantera.freely_propagating_premixed_flame`
- Source: Cantera official Python example, `Laminar flame speed calculation`
- Source URL: `https://cantera.org/stable/examples/python/onedim/adiabatic_flame.html`
- Mechanism: `h2o2.yaml`
- Pressure: `101325.0` Pa
- Unburned temperature: `300.0` K
- Reactants: `H2:1.1, O2:1, AR:5`
- Width: `0.03` m

## Validation Result

- Result: `passed`
- Local Cantera version: `3.2.0`
- Run output directory: `_results/cantera/c02_freely_propagating_premixed_flame/baseline`

## Benchmark Metrics

| Mode | Flame speed m/s | Peak temperature K | Flame position m | Grid points | Max heat release W/m3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mixture_averaged` | 0.7187425088779462 | 1857.2046351004196 | 0.021111328124999995 | 137 | 2507137368.430666 |
| `mixture_averaged_soret` | 0.6382291131982496 | 1853.616357090476 | 0.021117187499999995 | 143 | 2192612831.120387 |
| `multicomponent` | 0.7407122243874777 | 1867.6594984562525 | 0.021105468749999995 | 143 | 2606722938.023134 |
| `multicomponent_soret` | 0.6530703202267301 | 1854.7226272117396 | 0.021117187499999995 | 143 | 2238204470.8564863 |

## Scientific Interpretation

本案例验证的是一维自由传播预混氢气火焰的层流火焰速度和火焰结构。mixture-averaged 与 multicomponent transport 都给出正的 flame speed、有限峰值温度、充分网格点数和有界组分剖面。

启用 Soret diffusion 后，两个 transport model 下的 flame speed 均下降，且峰值热释放率降低。这个趋势与轻组分氢气火焰对热扩散效应敏感的预期一致，因此该 benchmark 可作为 C02 capability 的 baseline 验收样例。

## Generated Artifacts

- `premixed_flame_mixture_averaged.csv`
- `premixed_flame_mixture_averaged_soret.csv`
- `premixed_flame_multicomponent.csv`
- `premixed_flame_multicomponent_soret.csv`
- `premixed_flame_temperature_heat_release.png`
- `premixed_flame_major_species.png`
- `premixed_flame_run.log`
- `metrics.json`
- `validation_report.md`

## Follow-Up

下一步应补充至少 3 个扰动配置：未燃气温度扰动、混合气配比扰动、transport/Soret 模式扰动，并把趋势解释写入同类 validation report。
