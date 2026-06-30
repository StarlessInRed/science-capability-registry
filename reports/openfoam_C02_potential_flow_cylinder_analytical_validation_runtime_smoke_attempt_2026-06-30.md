# OpenFOAM C02 runtime smoke attempt

## Scope

- capability: `C02_potential_flow_cylinder_analytical_validation`
- gate: `smoke` attempt plus analytical validation
- matrix status: `failed`
- runtime profile: `openfoam_com_v2112`
- WSL distro: `Ubuntu-24.04`
- result root: `_results/openfoam/potential_flow_cylinder_analytical_validation/baseline_runtime_smoke_wsl_v2112`
- follow-up runtime config: `configs/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112.yaml`

## Runtime Outcome

- `blockMesh`: returncode `0`
- `potentialFoam -writePhi -writephi -writep`: returncode `0`
- solver log: started, no fatal error, residual records present
- generated artifacts: `manifest.json`, `metrics.json`, `validation.json`, solver logs, analytical field CSV, cylinder `Cp` CSV, and analytical error summary were generated under `_results/`

## Analytical Checks

- velocity L2 error: `1.1647355770764016` vs threshold `0.15` -> failed
- velocity Linf error: `6.912121724051375` vs threshold `0.5` -> failed
- pressure L2 error: `0.1366400904374664` vs threshold `0.2` -> passed
- `Cp` Linf error: `1.6228866742770676` vs threshold `0.6` -> failed
- field sample count: `1842`
- surface `Cp` sample count: `40`

## Status Conclusion

The OpenFOAM runtime path is executable, but the analytical validation gate fails. C02 remains `package_skeleton_created`; do not promote it to `benchmark_validated`.

## 2026-07-01 Follow-up

- A dedicated WSL smoke config now exists at `configs/openfoam/potential_flow_cylinder_analytical_validation/baseline_wsl_v2112.yaml`.
- The WSL smoke config keeps the existing analytical thresholds and adds `checkMesh` to the command sequence; it does not relax validation.
- Current evidence indicates the remaining issue is not solver startup. The next fix must address the finite-domain tutorial setup, Python/OpenFOAM cell-centre sampling parity, and the fact that current `Cp` is computed from cylinder owner-cell pressure rather than a defensible surface-pressure artifact.

## Next Work

- Review finite-domain and near-cylinder sampling policy before deciding whether the current thresholds or extraction points are scientifically appropriate.
- Run the mesh-refined case and compare error trends only after the baseline analytical comparison is defensible.
- Keep `Cp`, velocity, and pressure reference definitions config-visible.
