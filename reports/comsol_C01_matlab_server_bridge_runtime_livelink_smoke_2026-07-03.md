# COMSOL C01 MATLAB LiveLink smoke - 2026-07-03

## Scope

This report records the first successful COMSOL C01 MATLAB-to-COMSOL bridge smoke on the local machine.

The smoke used:

- `configs/comsol/matlab_server_bridge_runtime/local_livelink_smoke.yaml`
- environment-injected MATLAB executable path
- environment-injected COMSOL command path
- environment-injected LiveLink `mli` path
- an already running local COMSOL `mphserver`

## Result

- gate: `smoke`
- status: passed
- MATLAB batch return code: `0`
- runtime status: `matlab_livelink_smoke_passed`
- finite scalar: `1.0`
- scalar source: `mphevaluate(model, 'bridge_scalar')`
- runtime evidence path: `_results/comsol/matlab_server_bridge_runtime/local_livelink_smoke/`

## What This Proves

- MATLAB can start in batch mode from the configured environment boundary.
- LiveLink functions are reachable through the configured `COMSOL_MLI_DIR`.
- MATLAB can connect to a local COMSOL server through `mphstart`.
- A minimal COMSOL model can be created through `ModelUtil.create`.
- A COMSOL parameter can be evaluated through `mphevaluate` and exported as a finite canonical scalar.

## No-Claim Boundary

- This does not claim a COMSOL study solve.
- This does not claim field extraction through `mphglobal` or `mphinterp`.
- This does not claim official Application Library replay.
- This does not claim multiphysics correctness or benchmark validation.
- Local executable paths and server details remain runtime environment inputs and are not committed in configs.

## Next Gate

The next COMSOL capability is C02 `model_construction_api_contract`: create a minimal parameterized model tree from MATLAB, including component, geometry, material, mesh, and study tags, while retaining this C01 bridge as the runtime prerequisite.
