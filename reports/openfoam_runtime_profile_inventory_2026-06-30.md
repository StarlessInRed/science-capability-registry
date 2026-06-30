# OpenFOAM runtime profile inventory

## Scope

- date: 2026-06-30
- host backend: WSL `Ubuntu-24.04`
- action: lightweight runtime discovery only
- solver execution: not run

This report records runtime-profile discovery evidence. It does not promote any capability to cross-profile validation by itself.

## Registered Profiles

| profile_id | distribution | version | bashrc | status |
| --- | --- | --- | --- | --- |
| `openfoam_com_v2112` | OpenFOAM.com | `v2112` | `/opt/OpenFOAM-v2112/etc/bashrc` | registered and used for C01/C03/C06 local integration evidence |
| `openfoam_com_v2412` | OpenFOAM.com | `v2412` | `/usr/lib/openfoam/openfoam2412/etc/bashrc` | registered after bashrc, executable, and tutorial-root probe |

## v2412 Probe Evidence

The `openfoam_com_v2412` profile was added because the host probe confirmed:

- bashrc exists and sources successfully
- `WM_PROJECT_VERSION`: `v2412`
- `WM_PROJECT_DIR`: `/usr/lib/openfoam/openfoam2412`
- `FOAM_TUTORIALS`: `/usr/lib/openfoam/openfoam2412/tutorials`
- `FOAM_APPBIN`: `/usr/lib/openfoam/openfoam2412/platforms/linux64GccDPInt32Opt/bin`
- `FOAM_USER_APPBIN`: `/home/wenjian/OpenFOAM/wenjian-v2412/platforms/linux64GccDPInt32Opt/bin`
- required executables found: `blockMesh`, `checkMesh`, `icoFoam`, `simpleFoam`, `interFoam`, `setFields`, `postProcess`
- CHT executable found for later work: `chtMultiRegionSimpleFoam`
- C01/C03/C06 tutorial roots exist under the v2412 tutorial tree

## Discovered But Not Registered

| candidate | reason not registered in this pass |
| --- | --- |
| `openfoam_foundation_10` | Found under `/opt/OpenFOAM-10`, but not the immediate drop-in target for current OpenFOAM.com C01/C03/C06 assets. |
| `openfoam_foundation_11` | Found under `/opt/openfoam11`; Foundation tutorial layout differs and should be handled with a Foundation-specific profile task. |
| `openfoam_foundation_12` | Found under `/opt/openfoam12`; good future candidate for Foundation/CHT work, but not registered here because the current assets use OpenFOAM.com tutorial paths and single-region contracts. |
| `openfoam_foundation_7` | Detected on `Ubuntu-20.04`; old runtime, not part of the current Ubuntu-24.04 registry baseline. |

## Next Gate

The next validation step is targeted cross-profile smoke:

1. Add explicit v2412 run configs for C01, C03, and C06, or teach the runner to resolve tutorial roots from the selected runtime profile without duplicating native paths.
2. Run C01/C03/C06 smoke on `openfoam_com_v2412`.
3. Re-run C03/C06 native functionObject/sampling probes on v2412 to see whether the v2112 `sha1` limitation persists.
4. Register Foundation 12 only when a Foundation-specific case-layout contract is selected.
