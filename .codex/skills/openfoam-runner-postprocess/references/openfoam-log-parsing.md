# OpenFOAM Log Parsing

Parse logs defensively. Solver output differs by distribution, solver, and version.

## Required Signals

- solver started and exited successfully
- final simulation time or iteration
- final residuals by equation
- continuity or mass conservation errors when present
- Courant number when transient
- floating point exceptions, divergence messages, and fatal errors
- mesh check pass/fail if `checkMesh` ran

## Parser Policy

- Treat missing required signals as validation warnings or failures according to the capability card.
- Store raw logs even when parsing succeeds.
- Record parser version and known limitations in `metrics.json`.
- Do not infer scientific success from process exit code alone.
