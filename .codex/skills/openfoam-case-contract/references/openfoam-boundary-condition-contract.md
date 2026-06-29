# OpenFOAM Boundary Condition Contract

Boundary conditions are part of the scientific definition, not formatting details.

## Patch Contract

Each patch must define:

- patch name
- geometric role
- patch type from mesh
- field boundary condition per required field
- value or expression when required
- validation expectation, such as no-slip wall, fixed inlet velocity, or zero-gradient outlet

## Common Patterns

- 2D tutorial cases usually require `empty` front and back patches.
- Internal flow cases require inlet, outlet, and wall patch roles.
- External aerodynamics requires farfield or inlet/outlet roles plus wall treatment.
- VOF free-surface cases require phase fraction boundary rules and gravity orientation.

## Review Rule

Flag mismatches between mesh patch type and field boundary condition. A case with plausible fields but wrong patch semantics is not acceptable.
