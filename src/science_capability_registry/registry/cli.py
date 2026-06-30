"""Thin command line entrypoint for the science capability registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import load_catalog, resolve_capability
from .dispatcher import build_dispatch_plan, run_capability


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and dry-run registered science capabilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("plan", help="Print the validated dispatch plan.")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve one capability catalog entry.")
    resolve_parser.add_argument("capability_id")

    dry_run_parser = subparsers.add_parser("dry-run", help="Run a package dry-run through the registry dispatcher.")
    dry_run_parser.add_argument("capability_id")
    dry_run_parser.add_argument("--config", help="Override config path.")
    dry_run_parser.add_argument("--output-dir", help="Override output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = build_dispatch_plan()
        elif args.command == "resolve":
            load_catalog()
            result = resolve_capability(args.capability_id)
        elif args.command == "dry-run":
            result = run_capability(
                args.capability_id,
                config_path=Path(args.config) if args.config else None,
                output_dir=Path(args.output_dir) if args.output_dir else None,
                dry_run=True,
            )
        else:
            raise ValueError(f"Unsupported registry command: {args.command}")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    validation = result.get("validation") if isinstance(result, dict) else None
    if validation and not validation.get("passed", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
