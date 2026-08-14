#!/usr/bin/env python3
"""Normalize and concatenate planned segment clips with optional narration, music, and subtitles."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("project"), dict) or not isinstance(payload.get("segments"), list):
        raise ValueError("Invalid plan structure")
    return payload


def _escape_filter_path(path: Path) -> str:
    value = str(path.resolve()).replace("\\", "\\\\")
    for char in (":", "'", ",", "[", "]", ";"):
        value = value.replace(char, f"\\{char}")
    return value


def build_command(
    plan: dict[str, Any],
    segments_dir: Path,
    output: Path,
    narration: Path | None = None,
    bgm: Path | None = None,
    bgm_volume: float = 0.06,
    subtitles: Path | None = None,
    fontsdir: Path | None = None,
) -> list[str]:
    project = plan["project"]
    width = int(project["width"])
    height = int(project["height"])
    fps = int(project["fps"])
    total_duration = float(project["duration"])
    segments = plan["segments"]
    if not segments:
        raise ValueError("Plan has no segments")
    clips: list[tuple[Path, float]] = []
    for segment in segments:
        segment_id = str(segment["id"])
        clip = segments_dir / f"{segment_id}.mp4"
        if not clip.is_file():
            raise FileNotFoundError(f"Missing segment clip: {clip}")
        duration = float(segment["end"]) - float(segment["start"])
        clips.append((clip, duration))
    for optional in (narration, bgm, subtitles):
        if optional is not None and not optional.is_file():
            raise FileNotFoundError(f"Input file not found: {optional}")
    if fontsdir is not None and not fontsdir.is_dir():
        raise FileNotFoundError(f"Fonts directory not found: {fontsdir}")

    command = ["ffmpeg", "-hide_banner", "-y"]
    for clip, _ in clips:
        command.extend(["-i", str(clip.resolve())])
    narration_index = None
    bgm_index = None
    if narration:
        narration_index = len(clips)
        command.extend(["-i", str(narration.resolve())])
    if bgm:
        bgm_index = len(clips) + (1 if narration else 0)
        command.extend(["-i", str(bgm.resolve())])

    filters: list[str] = []
    for index, (_, duration) in enumerate(clips):
        filters.append(
            f"[{index}:v]trim=duration={duration:.6f},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={fps},format=yuv420p[v{index}]"
        )
    joined = "".join(f"[v{index}]" for index in range(len(clips)))
    filters.append(f"{joined}concat=n={len(clips)}:v=1:a=0[vcat]")
    video_label = "vcat"
    if subtitles:
        subtitle_filter = f"subtitles=filename='{_escape_filter_path(subtitles)}'"
        if fontsdir:
            subtitle_filter += f":fontsdir='{_escape_filter_path(fontsdir)}'"
        filters.append(f"[vcat]{subtitle_filter}[vout]")
        video_label = "vout"

    audio_label = None
    if narration_index is not None:
        filters.append(
            f"[{narration_index}:a]aresample=async=1:first_pts=0,atrim=0:{total_duration:.6f},"
            "asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=9[narr]"
        )
        audio_label = "narr"
    if bgm_index is not None:
        filters.append(
            f"[{bgm_index}:a]aloop=loop=-1:size=2147483647,atrim=0:{total_duration:.6f},"
            f"asetpts=PTS-STARTPTS,lowpass=f=4200,afade=t=in:st=0:d=0.4,"
            f"afade=t=out:st={max(0.0, total_duration - 1.6):.6f}:d=1.6,volume={bgm_volume:.4f}[music]"
        )
        if audio_label:
            filters.append("[narr][music]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[aout]")
            audio_label = "aout"
        else:
            audio_label = "music"

    command.extend(["-filter_complex", ";".join(filters), "-map", f"[{video_label}]"])
    if audio_label:
        command.extend(["-map", f"[{audio_label}]", "-c:a", "aac", "-b:a", "192k"])
    else:
        command.append("-an")
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-t",
            f"{total_duration:.6f}",
            str(output),
        ]
    )
    return command


def _verify(path: Path, expected_duration: float) -> dict[str, Any]:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or "ffprobe failed").strip())
    payload = json.loads(completed.stdout)
    actual = float((payload.get("format") or {}).get("duration") or 0)
    if abs(actual - expected_duration) > 0.15:
        raise RuntimeError(f"Assembled duration {actual:.3f}s differs from plan {expected_duration:.3f}s")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--segments", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--narration")
    parser.add_argument("--bgm")
    parser.add_argument("--bgm-volume", type=float, default=0.06)
    parser.add_argument("--subtitles")
    parser.add_argument("--fontsdir")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not 0 <= args.bgm_volume <= 1:
            raise ValueError("--bgm-volume must be between 0 and 1")
        plan_path = Path(args.plan).expanduser().resolve()
        plan = _load_plan(plan_path)
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.stem}.partial{output.suffix or '.mp4'}")
        command = build_command(
            plan,
            Path(args.segments).expanduser().resolve(),
            temporary,
            Path(args.narration).expanduser().resolve() if args.narration else None,
            Path(args.bgm).expanduser().resolve() if args.bgm else None,
            args.bgm_volume,
            Path(args.subtitles).expanduser().resolve() if args.subtitles else None,
            Path(args.fontsdir).expanduser().resolve() if args.fontsdir else None,
        )
        if args.dry_run:
            print(json.dumps({"ok": True, "command": command, "shell": shlex.join(command)}, ensure_ascii=False, indent=2))
            return 0
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            raise RuntimeError(f"ffmpeg exited with status {completed.returncode}")
        probe = _verify(temporary, float(plan["project"]["duration"]))
        os.replace(temporary, output)
        print(json.dumps({"ok": True, "output": str(output), "probe": probe}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
