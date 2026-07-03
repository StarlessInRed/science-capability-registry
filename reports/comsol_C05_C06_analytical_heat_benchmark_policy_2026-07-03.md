# COMSOL C05-C06 Analytical Heat Benchmark Policy - 2026-07-03

本报告记录 COMSOL C05-C06 从 smoke 走向 benchmark validation 的热传导 reference policy。它不是一次新的求解运行，也不提升 C05/C06 benchmark status。

## Candidate Order

| priority | candidate | role | promotion use |
| --- | --- | --- | --- |
| 1 | `Heat_Transfer_Module/Verification_Examples/thin_plate.mph` | small official Heat Transfer verification model | First official `.mph` heat replay after LiveLink domain activation passes. |
| 2 | `Heat_Transfer_Module/Tutorials,_Conduction/cylinder_conduction.mph` | simple steady conduction tutorial | Candidate for stationary solve and radial/axisymmetric field extraction. |
| 3 | generated heat rectangle manufactured solution | registry-controlled reference | Keep as a fully controlled fallback for unit/probe/constant-temperature validation. |

## Benchmark Promotion Rules

- C05 may only move beyond smoke after solver status, dataset creation, and at least one reference-aligned field/probe metric are present.
- C06 may only move beyond smoke after exported quantities include expression, unit, dataset/location, finite value fraction, and an error or conservation check.
- Official `.mph` replay is not enough by itself; the report must identify reference homology, expected values or trends, and tolerance policy.
- Generated heat-rectangle evidence can support runner correctness, but it is not an official heat-transfer benchmark.

## Current Boundary

C05-C06 currently have generated heat-rectangle smoke evidence and new official replay contracts. They do not yet have analytical field validation, double-v, or broader multiphysics correctness.
