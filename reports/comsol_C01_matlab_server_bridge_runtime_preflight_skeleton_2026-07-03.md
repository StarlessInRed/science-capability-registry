# COMSOL C01 MATLAB server bridge runtime preflight skeleton - 2026-07-03

## Scope

This report records the first executable package skeleton for `multiphysics.comsol.matlab_server_bridge_runtime`.

The package implements:

- schema validation for `configs/comsol/matlab_server_bridge_runtime/local_preflight.yaml`;
- generation of a minimal `matlab_bridge_smoke.m` LiveLink script candidate;
- environment/path preflight for `MATLAB_EXE`, `COMSOL_BIN`, and `COMSOL_MLI_DIR`;
- explicit separation between `dry_run_only`, `preflight_only`, and `matlab_livelink_smoke`;
- manifest, metrics, validation, and validation-report artifacts under `_results/comsol/matlab_server_bridge_runtime/`.

## Local Runtime Probe

The current host did not expose `matlab` or `comsol` on PATH, did not provide the required COMSOL/MATLAB environment variables, and did not expose common MATLAB/COMSOL install roots during the probe. Therefore the local run cannot be promoted to MATLAB LiveLink smoke.

Current gate: `static-readiness`.

## No-Claim Boundary

- No MATLAB batch execution is claimed.
- No COMSOL server connection is claimed.
- No LiveLink API import is claimed.
- No COMSOL study run, solver result, official model replay, or physics benchmark validation is claimed.
- Local executable, license, server, and Application Library paths remain environment-injected and are not committed.

## Next Gate

The next promotion requires a real runtime profile with `MATLAB_EXE`, `COMSOL_BIN`, and `COMSOL_MLI_DIR` set to existing local paths. After that, run the same config with `backend.type=matlab_livelink_smoke` and record the generated `_results` summary as a new stable report.

## Later Same-Day Update

This preflight blocker was superseded by `reports/comsol_C01_matlab_server_bridge_runtime_livelink_smoke_2026-07-03.md`, which records a passed MATLAB LiveLink smoke after the local runtime profile was supplied through environment variables.
