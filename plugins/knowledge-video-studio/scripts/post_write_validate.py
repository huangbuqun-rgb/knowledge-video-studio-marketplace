#!/usr/bin/env python3
"""PostToolUse hook: validate only video-plan.json and asset-ledger.json writes."""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from scripts.media_cli import validate_ledger  # noqa: E402
from scripts.validate_project import validate_plan  # noqa: E402


def _find_path(payload: object) -> str | None:
    if isinstance(payload, dict):
        for key in ("file_path", "path", "filePath"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        for value in payload.values():
            found = _find_path(value)
            if found:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = _find_path(value)
            if found:
                return found
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    value = _find_path(payload)
    if not value:
        return 0
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if path.name not in {"video-plan.json", "asset-ledger.json"} or not path.is_file():
        return 0
    try:
        if path.name == "video-plan.json":
            with path.open("r", encoding="utf-8") as handle:
                result = validate_plan(json.load(handle))
        else:
            result = validate_ledger(str(path), False)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps({"knowledge_video_validation": result}, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
