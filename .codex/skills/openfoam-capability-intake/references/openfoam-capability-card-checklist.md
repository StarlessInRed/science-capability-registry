# OpenFOAM Capability Card Checklist

Every OpenFOAM capability card must answer these questions.

## Scientific Definition

- What problem type is solved?
- Which governing model class is used?
- Which solver and distribution are assumed?
- Is the case steady, transient, laminar, turbulent, multiphase, compressible, or coupled?
- What material properties and model constants are required?

## Case Definition

- What geometry and mesh are required?
- Which patches exist and what boundary conditions apply to each field?
- What initial conditions are needed?
- Which schemes, solver tolerances, relaxation factors, time step controls, and functionObjects are required?

## Outputs

- Which fields, profiles, scalar metrics, and plots must be produced?
- Which outputs are required for automated validation?
- Which artifacts are useful only for human review?

## Validation

- What is the benchmark source?
- What metrics determine solver health?
- What physical constraints must hold?
- What perturbation trends are expected?
- What failure modes should be detected automatically?

## Integration

- What natural-language request should map to this capability?
- What structured config schema should be exposed?
- What runner backend is acceptable?
- What must an intern deliver for the capability owner to accept it?
