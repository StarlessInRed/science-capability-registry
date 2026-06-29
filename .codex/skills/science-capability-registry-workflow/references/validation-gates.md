# Validation Gates

Use one stable gate vocabulary across all capabilities.

| Tier | Trigger | Evidence |
| --- | --- | --- |
| `static-readiness` | Docs, asset cards, schemas, configs, dry-run paths | Schema tests pass, configs load, dry-run returns `validated_config=true` |
| `smoke` | Runner, CLI, output paths, postprocess | One baseline solver run produces nonempty artifacts and `validation.passed=true` |
| `targeted-regression` | Validation logic, metrics contract, bug fixes | Focused tests prove accepted examples pass and bad examples fail |
| `integration` | Baseline plus perturbation cases | Reports summarize baseline, at least three perturbations, and physical trends |
| `double-v` | Trusted external reference or physical parity is required | Error/tolerance/trend comparison against official values, paper values, or conservation constraints |
| `full-regression` | Release, broad refactor, shared contract change | All tests and representative solver cases pass, with unrun risks listed |

Do not create new gate names for individual capabilities.
