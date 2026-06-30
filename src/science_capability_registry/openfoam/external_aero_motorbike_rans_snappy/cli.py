"""Thin CLI entrypoint for OpenFOAM C04."""

from __future__ import annotations

import sys
from pathlib import Path

from .runner import run_from_config


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise ValueError("Usage: python -m science_capability_registry.openfoam.external_aero_motorbike_rans_snappy.cli <config.yaml>")
    run_from_config(Path(args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
