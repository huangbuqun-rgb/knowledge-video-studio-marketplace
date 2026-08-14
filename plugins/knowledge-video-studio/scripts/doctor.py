#!/usr/bin/env python3
"""Check dependencies without printing credentials."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any


def _version(command: list[str], timeout: int = 8) -> dict[str, Any]:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False, "version": None}
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (completed.stdout or completed.stderr).strip().splitlines()
        return {"available": completed.returncode == 0, "version": output[0] if output else None}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "version": None, "error": str(exc)}


def check_environment() -> dict[str, Any]:
    tools = {
        "python": {"available": True, "version": sys.version.split()[0]},
        "ffmpeg": _version(["ffmpeg", "-version"]),
        "ffprobe": _version(["ffprobe", "-version"]),
        "node": _version(["node", "--version"]),
        "npm": _version(["npm", "--version"]),
        "npx": _version(["npx", "--version"]),
    }
    node_text = str(tools["node"].get("version") or "")
    match = re.search(r"(\d+)", node_text)
    node_major = int(match.group(1)) if match else 0
    blockers = []
    if not tools["ffmpeg"]["available"] or not tools["ffprobe"]["available"]:
        blockers.append("FFmpeg and ffprobe are required for assembly and validation")
    if not tools["node"]["available"] or node_major < 22:
        blockers.append("Node.js 22 or newer is required for HyperFrames and recommended for Remotion")
    if not tools["npm"]["available"] or not tools["npx"]["available"]:
        blockers.append("npm and npx are required for motion renderer setup")
    return {
        "ok": not blockers,
        "tools": tools,
        "provider_keys": {
            "pexels": bool(os.getenv("PEXELS_API_KEY")),
            "pixabay": bool(os.getenv("PIXABAY_API_KEY")),
            "wikimedia": True,
        },
        "blockers": blockers,
        "notes": ["Missing stock API keys disable only that provider; their values are never reported."],
    }


def main() -> int:
    result = check_environment()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
