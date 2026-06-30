# OpenFOAM runtime profile sha1 probe report

## Scope

- date: 2026-06-30
- runtime profile: `openfoam_com_v2112`
- backend: WSL `Ubuntu-24.04`
- OpenFOAM version observed: `v2112`
- gate: `targeted-regression`
- purpose: classify whether C03/C06 native functionObject and sampling failures are only Windows-mounted-path failures or broader local runtime-profile failures.

## Probe Matrix

| probe | case source | execution path | commands | return codes | sha1 result |
| --- | --- | --- | --- | --- | --- |
| C03 pitzDaily native functionObjects | `/opt/OpenFOAM-v2112/tutorials/incompressible/simpleFoam/pitzDaily` | `/tmp/scr_c03_sha1_ext4_su5saQ/case` | `blockMesh`, `simpleFoam`, `simpleFoam -postProcess -latestTime -func wallShearStress`, `simpleFoam -postProcess -latestTime -func yPlus` | `blockMesh=0`, `simpleFoam=1`, `wallShearStress=1`, `yPlus=1` | `simpleFoam`, `wallShearStress`, and `yPlus` each emitted `sha1` fatal IO errors. |
| C06 damBreak native sampling | `/opt/OpenFOAM-v2112/tutorials/multiphase/interFoam/laminar/damBreak/damBreak` | `/tmp/scr_c06_sha1_ext4_EzIIDE/case` | `blockMesh`, `setFields`, `interFoam` with `system/sampling` included | `blockMesh=0`, `setFields=0`, `interFoam=1` | `interFoam` emitted `sha1` fatal IO error while sampling was enabled. |

## Evidence Lines

C03 ext4 probe:

- `log.simpleFoam:63: --> FOAM FATAL IO ERROR: (openfoam-2112)`
- `log.simpleFoam:64: error in IOstream "sha1" for operation Foam::Ostream& Foam::operator<<(Ostream&, int32_t)`
- `log.wallShearStress:35: --> FOAM FATAL IO ERROR: (openfoam-2112)`
- `log.yPlus:35: --> FOAM FATAL IO ERROR: (openfoam-2112)`

C06 ext4 probe:

- `log.interFoam:59: --> FOAM FATAL IO ERROR: (openfoam-2112)`
- `log.interFoam:60: error in IOstream "sha1" for operation Foam::Ostream& Foam::operator<<(Ostream&, const word&)`

## Conclusion

The C03 and C06 native functionObject/sampling failures are reproduced on WSL ext4 `/tmp` paths. They should be classified as a local `openfoam_com_v2112` WSL runtime-profile limitation, not merely as a Windows-mounted repository-path limitation.

For this profile, C03 wall shear/yPlus and C06 alpha/gauge evidence should continue to use the Python final-field parsers already covered by the integration matrices. These Python postprocessors are acceptable for `integration` evidence but do not support `double-v` claims by themselves.

## Next Validation Work

- Test the same native functionObject/sampling probes on a second runtime profile, such as Foundation OpenFOAM 13 or another OpenFOAM.com installation.
- If native output succeeds on another profile, add profile-specific parity tests against the Python postprocess outputs.
- Do not promote C03/C06 to `double-v` until either native parity evidence or independent reference data exists.
