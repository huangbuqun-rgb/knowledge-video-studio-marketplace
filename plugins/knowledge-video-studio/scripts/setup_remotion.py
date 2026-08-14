#!/usr/bin/env python3
"""Copy the bundled JSON-driven Remotion starter to a new scene directory."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plugin_root = Path(__file__).resolve().parents[1]
    source = plugin_root / "assets" / "remotion-engine"
    output = Path(args.output).expanduser().resolve()
    if not source.is_dir():
        print(json.dumps({"ok": False, "error": f"Bundled template missing: {source}"}), file=sys.stderr)
        return 1
    if output.exists() and any(output.iterdir()):
        print(json.dumps({"ok": False, "error": f"Refusing to overwrite non-empty directory: {output}"}), file=sys.stderr)
        return 1
    if output.exists():
        output.rmdir()
    shutil.copytree(source, output)
    print(json.dumps({"ok": True, "project": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
