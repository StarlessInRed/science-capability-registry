# OpenFOAM Field And Dimension Contract

The schema must make field names, dimensions, and physical bounds explicit.

## Required Field Metadata

- field name, such as `U`, `p`, `T`, `k`, `omega`, `epsilon`, or `alpha.water`
- OpenFOAM dimensions
- internal field value
- boundary field mapping by patch
- expected min and max bounds when physically meaningful
- whether the field is scalar, vector, or tensor

## Common Checks

- Velocity and pressure fields exist for incompressible flow.
- Turbulence fields exist when a RANS model is selected.
- Volume fraction fields are bounded in `[0, 1]` for VOF cases.
- Temperature and density remain positive.
- Dimensions match the selected solver family.

## Failure Policy

Reject configs that omit dimensions or rely on implicit tutorial defaults for fields that affect physics.
