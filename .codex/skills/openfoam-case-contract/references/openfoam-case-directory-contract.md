# OpenFOAM Case Directory Contract

Generated cases should preserve OpenFOAM case anatomy while keeping repository config canonical.

## Generated Case Layout

- `0/`: initial and boundary field files.
- `constant/`: mesh, transport properties, turbulence properties, thermophysical properties, phase properties, and other model dictionaries.
- `system/`: `controlDict`, `fvSchemes`, `fvSolution`, decomposition settings, mesh generation dictionaries, and functionObjects.

## Manifest

Dry run must write a manifest with:

- source config path and schema id
- OpenFOAM distribution and version expectation
- solver command sequence
- generated file list
- mesh command sequence
- postprocess command sequence
- expected outputs
- validation metrics and thresholds
- backend selection

## Canonical Source Rule

Do not make copied tutorial folders the long-term source of truth. The canonical source is the schema plus config. Generated dictionaries are artifacts.
