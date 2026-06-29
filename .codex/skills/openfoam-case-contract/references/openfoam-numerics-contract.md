# OpenFOAM Numerics Contract

Numerical controls must be visible in config.

## Required Sections

- solver name
- steady or transient mode
- `controlDict` time settings, write interval, and adjustable time step rules
- `fvSchemes` discretization choices
- `fvSolution` solvers, tolerances, relaxation factors, and residual controls
- turbulence model and wall treatment when applicable
- functionObjects for probes, forces, field extrema, residuals, and yPlus when applicable

## Validation Hooks

Expose thresholds for:

- final residuals by equation
- continuity or mass conservation error
- maximum Courant number for transient runs
- mesh quality thresholds
- boundedness of key fields
- capability-specific reference metrics

## Rule

Do not hide solver tolerance, time step, or scheme choices in Python constants. They are scientific settings and belong in config.
