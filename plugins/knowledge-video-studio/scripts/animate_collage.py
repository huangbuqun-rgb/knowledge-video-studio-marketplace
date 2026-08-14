#!/usr/bin/env python3
"""Animate a single editorial poster into a deterministic MP4 using FFmpeg."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def build_filter(width: int, height: int, fps: int, duration: float, motion: str) -> str:
    frames = max(1, round(fps * duration))
    pre = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    if motion == "push-in":
        zoom = "min(zoom+0.0009,1.09)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pull-out":
        zoom = "if(eq(on,1),1.09,max(1.0,zoom-0.0009))"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan-left":
        zoom = "1.08"
        x = f"(iw-iw/zoom)*(1-on/{frames})"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan-right":
        zoom = "1.08"
        x = f"(iw-iw/zoom)*(on/{frames})"
        y = "ih/2-(ih/zoom/2)"
    else:
        zoom = "1.0"
        x = "0"
        y = "0"
    return (
        f"{pre},zoompan=z='{zoom}':x='{x}':y='{y}':d={frames}:s={width}x{height}:fps={fps},"
        "format=yuv420p"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--motion", choices=["push-in", "pull-out", "pan-left", "pan-right", "hold"], default="push-in")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        print(json.dumps({"ok": False, "error": f"Input image not found: {source}"}), file=sys.stderr)
        return 1
    if args.duration <= 0 or args.width < 320 or args.height < 320 or args.fps not in {24, 25, 30, 50, 60}:
        print(json.dumps({"ok": False, "error": "Invalid duration, dimensions, or fps"}), file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-loop",
        "1",
        "-i",
        str(source),
        "-vf",
        build_filter(args.width, args.height, args.fps, args.duration, args.motion),
        "-t",
        f"{args.duration:.6f}",
        "-r",
        str(args.fps),
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    if args.dry_run:
        print(json.dumps({"ok": True, "command": command, "shell": shlex.join(command)}, ensure_ascii=False, indent=2))
        return 0
    completed = subprocess.run(command, check=False)
    if completed.returncode or not output.is_file() or output.stat().st_size == 0:
        print(json.dumps({"ok": False, "error": f"ffmpeg exited with status {completed.returncode}"}), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
