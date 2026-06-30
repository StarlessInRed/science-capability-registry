"""Command line entrypoint for Gmsh C01."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or dry-run the Gmsh C01 parametric mesh-generation capability.")
    parser.add_argument("--config", required=True, help="Path to a Gmsh C01 YAML config.")
    parser.add_argument("--output-dir", help="Override output directory.")
    parser.add_argument("--backend", help="Override backend type.")
    parser.add_argument("--dry-run", action="store_true", help="Generate .geo and manifest without running Gmsh.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(config_path=Path(args.config), output_dir=Path(args.output_dir) if args.output_dir else None, dry_run=args.dry_run, backend=args.backend)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    validation = result.get("validation")
    if validation and not validation.get("passed", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
