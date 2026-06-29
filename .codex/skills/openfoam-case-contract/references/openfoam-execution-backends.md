# OpenFOAM Execution Backends

OpenFOAM execution depends on the host. Keep backend selection explicit.

## Backend Values

- `dry_run_only`: generate and validate files without running OpenFOAM.
- `native_linux`: run commands directly on a Linux shell.
- `wsl`: run commands through WSL from Windows.
- `docker`: run commands inside a configured OpenFOAM image.

## Backend Contract

Each backend must define:

- command prefix or container image
- working directory mapping
- OpenFOAM environment setup command
- timeout policy
- parallel execution support
- version check command

## Restrictions

Do not hardcode user-specific paths, WSL distro names, Docker image tags, or shell startup files in package code. Put those choices in config or environment discovery.
