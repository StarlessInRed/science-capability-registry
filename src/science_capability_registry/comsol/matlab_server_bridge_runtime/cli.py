"""Command line entrypoint for COMSOL C01."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .runner import run


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: comsol-c01 <config.yaml> [output_dir] [--dry-run]", file=sys.stderr)
        return 2
    dry_run = "--dry-run" in args
    clean_args = [arg for arg in args if arg != "--dry-run"]
    try:
        result = run(
            config_path=Path(clean_args[0]),
            output_dir=Path(clean_args[1]) if len(clean_args) > 1 else None,
            dry_run=dry_run,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("validation", {}).get("passed", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
