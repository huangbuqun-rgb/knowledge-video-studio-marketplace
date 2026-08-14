#!/usr/bin/env python3
"""Dependency-free MCP stdio server for rights-described media search and download."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from scripts.doctor import check_environment  # noqa: E402
from scripts.media_cli import (  # noqa: E402
    MediaError,
    download_media,
    register_local_media,
    search_media,
    validate_ledger,
)


TOOLS = [
    {
        "name": "search_media",
        "description": "Search Pexels, Pixabay, and/or Wikimedia Commons and return candidates with rights metadata. Auto mode skips providers whose API key is missing.",
        "inputSchema": {
            "type": "object",
            "required": ["queries"],
            "properties": {
                "queries": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "provider": {"type": "string", "enum": ["auto", "pexels", "pixabay", "wikimedia"], "default": "auto"},
                "orientation": {"type": "string", "enum": ["landscape", "portrait", "square", "any"], "default": "landscape"},
                "media_type": {"type": "string", "enum": ["video", "image", "any"], "default": "video"},
                "per_page": {"type": "integer", "minimum": 1, "maximum": 50, "default": 8}
            }
        }
    },
    {
        "name": "download_media",
        "description": "Download one candidate to the project and atomically add its license, source, attribution, and SHA-256 to asset-ledger.json.",
        "inputSchema": {
            "type": "object",
            "required": ["item", "output_dir", "ledger_path", "segment_id"],
            "properties": {
                "item": {"type": "object"},
                "output_dir": {"type": "string"},
                "ledger_path": {"type": "string"},
                "segment_id": {"type": "string"},
                "filename": {"type": "string"}
            }
        }
    },
    {
        "name": "register_local_media",
        "description": "Register a user-supplied local media file in the same rights ledger without copying it.",
        "inputSchema": {
            "type": "object",
            "required": ["file_path", "ledger_path", "segment_id", "creator", "rights_basis"],
            "properties": {
                "file_path": {"type": "string"},
                "ledger_path": {"type": "string"},
                "segment_id": {"type": "string"},
                "creator": {"type": "string"},
                "rights_basis": {"type": "string"}
            }
        }
    },
    {
        "name": "validate_ledger",
        "description": "Validate required rights metadata and optionally verify local files and SHA-256 checksums.",
        "inputSchema": {
            "type": "object",
            "required": ["ledger_path"],
            "properties": {
                "ledger_path": {"type": "string"},
                "verify_files": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "doctor",
        "description": "Check local video dependencies and report whether provider keys are configured without exposing their values.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


def _tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "search_media":
        return search_media(
            arguments.get("queries") or [],
            arguments.get("provider", "auto"),
            arguments.get("orientation", "landscape"),
            arguments.get("media_type", "video"),
            int(arguments.get("per_page", 8)),
        )
    if name == "download_media":
        return download_media(
            arguments.get("item") or {},
            str(arguments.get("output_dir") or ""),
            str(arguments.get("ledger_path") or ""),
            str(arguments.get("segment_id") or ""),
            arguments.get("filename"),
        )
    if name == "register_local_media":
        return register_local_media(
            str(arguments.get("file_path") or ""),
            str(arguments.get("ledger_path") or ""),
            str(arguments.get("segment_id") or ""),
            str(arguments.get("creator") or ""),
            str(arguments.get("rights_basis") or ""),
        )
    if name == "validate_ledger":
        return validate_ledger(str(arguments.get("ledger_path") or ""), bool(arguments.get("verify_files", False)))
    if name == "doctor":
        return check_environment()
    raise MediaError(f"Unknown tool: {name}")


def _response(request_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    return payload


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion") or "2025-03-26"
        return _response(
            request_id,
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "knowledge-video-media", "version": "1.0.0"},
                "instructions": "Search and download only rights-described media; preserve the returned license ledger."
            },
        )
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            value = _tool_call(str(params.get("name") or ""), params.get("arguments") or {})
            is_error = value.get("ok") is False if isinstance(value, dict) else False
            return _response(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
                    "isError": is_error,
                    "structuredContent": value,
                },
            )
        except Exception as exc:
            value = {"ok": False, "error": str(exc)}
            return _response(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
                    "isError": True,
                    "structuredContent": value,
                },
            )
    return _response(request_id, error={"code": -32601, "message": f"Method not found: {method}"})


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            reply = _handle(message)
            if reply is not None:
                sys.stdout.write(json.dumps(reply, ensure_ascii=False, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stderr.write(f"knowledge-video-media: {exc}\n")
            sys.stderr.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
