# OpenFOAM C01/C03/C06 double-v policy - 2026-07-01

## Scope

本报告记录 C01, C03, and C06 的 double-v 后续策略。三者已经有 registry-local validation and v2412 cross-profile replay evidence, but the remaining work is external or independent verification.

## C01

Current state:

- local integration benchmark is retained
- v2412 replay has passed
- external centerline reference is missing
- mesh/time independence evidence is missing

Required before double-v claim:

- centerline velocity reference data, such as a Ghia-style benchmark table
- configured velocity-error thresholds
- mesh/time independence or equivalent independent comparison

## C03

Current state:

- local pitzDaily RANS evidence is retained
- v2412 replay has passed
- wallShearStress/yPlus remain proxy or incomplete
- external backward-facing-step RANS reference is missing

Required before double-v claim:

- native or independently cross-validated wallShearStress/yPlus evidence
- reattachment length and pressure-drop reference comparison
- wall-function validity bounds

## C06

Current state:

- local short-horizon dam-break validation is retained
- v2412 replay has passed
- v2412 native sampleSets artifact evidence has passed
- v2412 1.0 s full-horizon runtime has passed
- sampleSets VTP field-value parity is missing
- external full-horizon free-surface reference comparison is missing

Required before double-v claim:

- native sampleSets value parity or independent sampling parity
- external dam-break reference comparison

## Decision

The v2412 replay is cross-profile robustness evidence, not external double-v. It should not weaken the existing local benchmark status, and it should not be presented as completed double-v.
