# Cantera C01 Validation Report: baseline

## Case

- Capability: `combustion.cantera.constant_pressure_ignition`
- Mechanism: `h2o2.yaml`
- Reactor model: `ideal_gas_constant_pressure`
- Initial temperature: `1001.0` K
- Pressure: `101325.0` Pa
- Composition: `H2:2,O2:1,N2:4`

## Ignition Metrics

- Ignition delay: `0.00031501152054322335` s
- Ignition delay method: `max_temperature_derivative`
- Final temperature: `2665.6598489389216` K
- Temperature rise: `1664.6598489389216` K
- Maximum dT/dt: `68580309.15212761` K/s
- OH peak mole fraction: `0.023870730041095623`
- Maximum relative pressure error: `2.872324742830861e-16`
- Time points: `162`

## Validation

- Passed: `True`

- `PASS` `profile.present`: Metrics include raw time-series profile.
- `PASS` `profile.equal_lengths`: Profile column lengths: {'time_s': 162, 'time_ms': 162, 'temperature_k': 162, 'pressure_pa': 162, 'internal_energy_j_kg': 162, 'enthalpy_j_kg': 162, 'X_OH': 162, 'X_H': 162, 'X_H2': 162, 'X_O2': 162, 'X_H2O': 162}.
- `PASS` `profile.column.time_s`: Column time_s length is 162.
- `PASS` `profile.column.time_ms`: Column time_ms length is 162.
- `PASS` `profile.column.temperature_k`: Column temperature_k length is 162.
- `PASS` `profile.column.pressure_pa`: Column pressure_pa length is 162.
- `PASS` `profile.column.internal_energy_j_kg`: Column internal_energy_j_kg length is 162.
- `PASS` `profile.column.enthalpy_j_kg`: Column enthalpy_j_kg length is 162.
- `PASS` `profile.column.X_OH`: Column X_OH length is 162.
- `PASS` `profile.column.X_H`: Column X_H length is 162.
- `PASS` `profile.column.X_H2`: Column X_H2 length is 162.
- `PASS` `profile.column.X_O2`: Column X_O2 length is 162.
- `PASS` `profile.column.X_H2O`: Column X_H2O length is 162.
- `PASS` `profile.time_monotonic`: time_s is strictly increasing.
- `PASS` `integration.max_time_step`: Maximum saved time step is 1.00931e-05 s.
- `PASS` `integration.time_points`: Time point count is 162.
- `PASS` `integration.end_time`: End time is 0.00100629 s for requested 0.001 s.
- `PASS` `temperature.initial_matches_config`: Initial profile temperature is 1001 K.
- `PASS` `temperature.final_reference_range`: Expected 2500.0 K <= final <= 3200.0 K; got 2665.66 K.
- `PASS` `temperature.rise`: Temperature rise is 1664.66 K.
- `PASS` `ignition_delay.finite_positive`: Ignition delay is 0.000315012 s.
- `PASS` `ignition_delay.reference_range`: Expected 1e-05 s <= tau <= 0.001 s; got 0.000315012 s.
- `PASS` `temperature.max_derivative_positive`: Maximum dT/dt is 6.85803e+07 K/s.
- `PASS` `temperature.advance_limit`: Maximum saved temperature step is 20 K.
- `PASS` `pressure.constant`: Maximum relative pressure error is 2.87232e-16.
- `PASS` `ignition_delay.method`: Summary method is max_temperature_derivative.
- `PASS` `ignition_delay.not_boundary`: Ignition index is 51 in 162 saved points.
- `PASS` `species_bounds.OH`: OH mole fraction range is [0, 0.0238707].
- `PASS` `species_bounds.H`: H mole fraction range is [0, 0.0879119].
- `PASS` `species_bounds.H2`: H2 mole fraction range is [0.032258, 0.285714].
- `PASS` `species_bounds.O2`: O2 mole fraction range is [0.0118916, 0.142857].
- `PASS` `species_bounds.H2O`: H2O mole fraction range is [0, 0.27723].
- `PASS` `artifact.ignition_profile.csv`: Artifact path: E:\Projects\science-capability-registry\_results\cantera\c01_constant_pressure_ignition\baseline\ignition_profile.csv
- `PASS` `artifact.ignition_temperature_species.png`: Artifact path: E:\Projects\science-capability-registry\_results\cantera\c01_constant_pressure_ignition\baseline\ignition_temperature_species.png
- `PASS` `artifact.ignition_run.log`: Artifact path: E:\Projects\science-capability-registry\_results\cantera\c01_constant_pressure_ignition\baseline\ignition_run.log
- `PASS` `artifact.metrics.json`: Artifact path: E:\Projects\science-capability-registry\_results\cantera\c01_constant_pressure_ignition\baseline\metrics.json
- `PASS` `artifact.validation_report.md`: Artifact path: E:\Projects\science-capability-registry\_results\cantera\c01_constant_pressure_ignition\baseline\validation_report.md
