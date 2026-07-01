# OpenFOAM C05 external Strouhal reference policy - 2026-07-01

## Scope

- capability: `C05_transient_cylinder_vortex_shedding`
- reference-bound config: `configs/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_external_reference_wsl_v2412.yaml`
- existing runtime result: `_results/openfoam/transient_cylinder_vortex_shedding/runtime_forcecoeffs_strouhal_wsl_v2412/`
- runtime profile: `openfoam_com_v2412`

## Selected Reference

The selected external reference family is free flow past a circular cylinder at low Reynolds number:

- Jiang, H. and Cheng, L. (2017), `Strouhal-Reynolds number relationship for flow past a circular cylinder`, Journal of Fluid Mechanics 832, 170-188.
- Source URL: `https://scispace.com/pdf/strouhal-reynolds-number-relationship-for-flow-past-a-16pnft2xtp.pdf`
- Definition: `St = fD/U`, where `f` is the fluctuating-lift shedding frequency, `D` is cylinder diameter, and `U` is incoming velocity.
- Target range retained for this registry: `[0.16, 0.24]`.

This reference is comparable, but not a direct geometry match. The paper uses a far-field free-cylinder DNS setup; the current OpenFOAM `cylinder2D` tutorial domain is much shorter:

- inlet distance: about `5.06D`
- outlet distance: about `9.33D`
- crossflow distance: about `5D`

The source describes far-field distances of `20D` to inlet/crossflow boundaries and `30D` to outlet for the standard Re <= 300 setup. Therefore, selected reference provenance closes the policy gap, but it does not by itself close validation.

## Current Evidence

The v2412 native forceCoeffs runtime remains failed against the retained target:

- final time: `7.999830037232331`
- max Courant: `0.4933629867730658`
- coefficient rows: `8001`
- FFT analysis window: `6 s`
- selected FFT Strouhal: `0.13999999999997398`
- dominant FFT candidates: `0.14`, `0.12`, `0.16`
- failed check: `postprocess.strouhal_target_range`

The third FFT candidate falls at `St~0.16`, so the current result should not be interpreted as a settled physical contradiction. It is a sensitivity and signal-selection problem.

## Status

C05 remains `validation_failed`.

The reference-policy task is now closed at the contract level: the selected source, definition, range, and geometry-match boundary are encoded in schema and config. Benchmark promotion still requires at least one of:

- domain/mesh/time-step sensitivity that moves the native forceCoeffs FFT into the selected range, or
- a reviewed independent frequency extraction method that explains why the OpenFOAM tutorial setup should use a different target.
