"""Command line entrypoint for Fluent official replay manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .runner import run


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("Usage: fluent-replay-manifest <config.yaml> [output_dir]", file=sys.stderr)
        return 2
    try:
        result = run(
            config_path=Path(args[0]),
            output_dir=Path(args[1]) if len(args) > 1 else None,
            dry_run=True,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("validation", {}).get("passed", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
