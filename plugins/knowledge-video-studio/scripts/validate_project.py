#!/usr/bin/env python3
"""Validate the video plan, rendered segments, and optional rights ledger."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from scripts.media_cli import validate_ledger  # noqa: E402


MODES = {"stock", "hyperframes", "remotion", "editorial_collage", "hybrid"}
TRANSITIONS = {"cut", "fade", "dip_to_color", "match_cut", "chapter"}
FPS_VALUES = {24, 25, 30, 50, 60}


def _issue(report: dict[str, Any], severity: str, code: str, message: str, segment_id: str | None = None) -> None:
    item = {"severity": severity, "code": code, "message": message}
    if segment_id:
        item["segment_id"] = segment_id
    report["issues"].append(item)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ffprobe(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise RuntimeError((completed.stderr or "ffprobe failed").strip())
    return json.loads(completed.stdout)


def _fps(rate: str | None) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        numerator, denominator = rate.split("/", 1)
        return float(numerator) / float(denominator)
    return float(rate)


def validate_plan(plan: dict[str, Any], segments_dir: Path | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": True, "issues": [], "metrics": {}}
    if not isinstance(plan, dict):
        _issue(report, "error", "plan_not_object", "Plan root must be an object")
        report["ok"] = False
        return report
    if plan.get("schema_version") != "1.0":
        _issue(report, "error", "schema_version", "schema_version must be '1.0'")
    project = plan.get("project")
    segments = plan.get("segments")
    if not isinstance(project, dict):
        _issue(report, "error", "project_missing", "project must be an object")
        project = {}
    if not isinstance(segments, list) or not segments:
        _issue(report, "error", "segments_missing", "segments must be a non-empty array")
        segments = []

    for field in ("title", "language", "width", "height", "fps", "duration", "visual_system"):
        if field not in project:
            _issue(report, "error", "project_field_missing", f"project.{field} is required")
    width = project.get("width")
    height = project.get("height")
    fps = project.get("fps")
    duration = project.get("duration")
    quality_profile = project.get("quality_profile", "standard")
    if quality_profile not in {"standard", "editorial-premium"}:
        _issue(report, "error", "quality_profile", "project.quality_profile must be 'standard' or 'editorial-premium'")
    premium = quality_profile == "editorial-premium"
    if not isinstance(width, int) or width < 320:
        _issue(report, "error", "invalid_width", "project.width must be an integer >= 320")
    if not isinstance(height, int) or height < 320:
        _issue(report, "error", "invalid_height", "project.height must be an integer >= 320")
    if fps not in FPS_VALUES:
        _issue(report, "error", "invalid_fps", f"project.fps must be one of {sorted(FPS_VALUES)}")
    if not _number(duration) or float(duration) <= 0:
        _issue(report, "error", "invalid_duration", "project.duration must be a positive finite number")
        duration = 0.0
    visual = project.get("visual_system")
    anchor_id = ""
    if not isinstance(visual, dict):
        _issue(report, "error", "visual_system", "project.visual_system must be an object")
    else:
        if not isinstance(visual.get("palette"), list) or len(visual.get("palette", [])) < 2:
            _issue(report, "error", "visual_palette", "visual_system.palette needs at least two colors")
        if not isinstance(visual.get("typefaces"), list) or not visual.get("typefaces"):
            _issue(report, "error", "visual_typefaces", "visual_system.typefaces needs at least one typeface")
        if not str(visual.get("motion_character") or "").strip():
            _issue(report, "error", "motion_character", "visual_system.motion_character is required")
        anchor = visual.get("anchor")
        if premium:
            if not isinstance(anchor, dict):
                _issue(report, "error", "visual_anchor", "editorial-premium requires visual_system.anchor")
            else:
                anchor_id = str(anchor.get("id") or "").strip()
                for field in ("id", "description", "continuity_strategy"):
                    if not str(anchor.get(field) or "").strip():
                        _issue(report, "error", "visual_anchor", f"editorial-premium requires visual_system.anchor.{field}")

    voice = project.get("voice_strategy")
    if premium:
        if not isinstance(voice, dict):
            _issue(report, "error", "voice_strategy", "editorial-premium requires project.voice_strategy")
        else:
            if voice.get("one_take") is not True:
                _issue(report, "error", "voice_one_take", "editorial-premium requires one continuous narration take")
            if not str(voice.get("speaker") or "").strip():
                _issue(report, "error", "voice_speaker", "editorial-premium requires one named speaker profile")
            if not str(voice.get("direction") or "").strip():
                _issue(report, "error", "voice_direction", "editorial-premium requires a reusable voice direction")
            target_rate = voice.get("target_chars_per_second")
            if not isinstance(target_rate, list) or len(target_rate) != 2 or not all(_number(item) for item in target_rate):
                _issue(report, "error", "voice_rate", "voice_strategy.target_chars_per_second must contain [min, max]")
        audio_strategy = project.get("audio_strategy")
        if not isinstance(audio_strategy, dict):
            _issue(report, "error", "audio_strategy", "editorial-premium requires project.audio_strategy")
        else:
            if not _number(audio_strategy.get("voice_target_lufs")):
                _issue(report, "error", "voice_target_lufs", "audio_strategy.voice_target_lufs is required")
            bgm_gap = audio_strategy.get("bgm_below_voice_db")
            if not _number(bgm_gap) or float(bgm_gap) < 18:
                _issue(report, "error", "bgm_voice_gap", "editorial-premium requires music at least 18 dB below narration")
            sfx_limit = audio_strategy.get("sfx_max_per_40s")
            if not isinstance(sfx_limit, int) or isinstance(sfx_limit, bool) or sfx_limit > 3:
                _issue(report, "error", "sfx_limit", "editorial-premium allows at most 3 sound effects per 40 seconds")

    ids: set[str] = set()
    previous_end = 0.0
    mode_seconds = {mode: 0.0 for mode in MODES}
    mode_switches = 0
    previous_mode: str | None = None
    hero_scene_id = str(project.get("hero_scene_id") or "").strip()
    hero_duration: float | None = None
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            _issue(report, "error", "segment_not_object", f"segments[{index}] must be an object")
            continue
        segment_id = str(segment.get("id") or "")
        if not segment_id or not re.fullmatch(r"[A-Za-z0-9_-]+", segment_id):
            _issue(report, "error", "segment_id", "Segment id must contain only letters, digits, underscores, or hyphens", segment_id or None)
        elif segment_id in ids:
            _issue(report, "error", "segment_duplicate", "Duplicate segment id", segment_id)
        ids.add(segment_id)
        start = segment.get("start")
        end = segment.get("end")
        if not _number(start) or not _number(end) or float(end) <= float(start if _number(start) else 0):
            _issue(report, "error", "segment_timing", "Segment start/end must be finite and end > start", segment_id)
            continue
        start = float(start)
        end = float(end)
        segment_duration = end - start
        if segment_id == hero_scene_id:
            hero_duration = segment_duration
        if start < previous_end - 0.02:
            _issue(report, "error", "segment_overlap", f"Segment starts before previous end {previous_end:.3f}", segment_id)
        elif start > previous_end + 0.08:
            _issue(report, "error", "segment_gap", f"Timeline gap of {start - previous_end:.3f}s", segment_id)
        previous_end = max(previous_end, end)
        if segment_duration < 0.5:
            _issue(report, "warning", "segment_too_short", f"Segment is only {segment_duration:.2f}s", segment_id)
        if segment_duration > 20:
            _issue(report, "warning", "segment_too_long", f"Segment is {segment_duration:.2f}s; consider a semantic split", segment_id)
        mode = segment.get("visual_mode")
        if mode not in MODES:
            _issue(report, "error", "visual_mode", f"Unsupported visual_mode: {mode}", segment_id)
        else:
            mode_seconds[mode] += segment_duration
            if previous_mode is not None and mode != previous_mode:
                mode_switches += 1
            previous_mode = mode
        if not str(segment.get("narration") or "").strip():
            _issue(report, "warning", "empty_narration", "Segment narration is empty", segment_id)
        if premium:
            if str(segment.get("visual_anchor_id") or "").strip() != anchor_id:
                _issue(report, "error", "segment_visual_anchor", "Every editorial-premium segment must use the project visual anchor", segment_id)
            if segment.get("evidence_role") not in {"evidence", "context", "mechanism", "mood", "none"}:
                _issue(report, "error", "evidence_role", "editorial-premium requires an evidence_role for every segment", segment_id)
        for field in ("intent", "reason", "transition", "status"):
            if not str(segment.get(field) or "").strip():
                _issue(report, "error", "segment_field_missing", f"Segment {field} is required", segment_id)
        if segment.get("transition") not in TRANSITIONS:
            _issue(report, "error", "transition", f"Unsupported transition: {segment.get('transition')}", segment_id)
        media = segment.get("media")
        render = segment.get("render")
        if mode in {"stock", "hybrid"}:
            queries = media.get("queries") if isinstance(media, dict) else None
            if not isinstance(queries, list) or not any(str(item).strip() for item in queries):
                _issue(report, "error", "media_queries", "stock/hybrid segment needs media.queries", segment_id)
        if mode in {"hyperframes", "remotion", "editorial_collage", "hybrid"}:
            brief = render.get("brief") if isinstance(render, dict) else None
            if not str(brief or "").strip():
                _issue(report, "error", "render_brief", "motion/hybrid segment needs render.brief", segment_id)

        if segments_dir is not None and segment_id:
            clip = segments_dir / f"{segment_id}.mp4"
            if not clip.is_file():
                _issue(report, "error", "segment_file_missing", f"Missing rendered clip: {clip}", segment_id)
            else:
                try:
                    probe = _ffprobe(clip)
                    video_streams = [item for item in probe.get("streams", []) if item.get("codec_type") == "video"]
                    if not video_streams:
                        _issue(report, "error", "segment_no_video", "Clip has no video stream", segment_id)
                    else:
                        stream = video_streams[0]
                        if isinstance(width, int) and stream.get("width") != width:
                            _issue(report, "error", "segment_width", f"Clip width {stream.get('width')} != {width}", segment_id)
                        if isinstance(height, int) and stream.get("height") != height:
                            _issue(report, "error", "segment_height", f"Clip height {stream.get('height')} != {height}", segment_id)
                        actual_fps = _fps(stream.get("avg_frame_rate"))
                        if fps in FPS_VALUES and abs(actual_fps - float(fps)) > 0.05:
                            _issue(report, "error", "segment_fps", f"Clip fps {actual_fps:.3f} != {fps}", segment_id)
                    actual_duration = float((probe.get("format") or {}).get("duration") or 0)
                    if abs(actual_duration - segment_duration) > max(0.12, 2 / float(fps or 30)):
                        _issue(report, "error", "segment_duration", f"Clip duration {actual_duration:.3f}s != planned {segment_duration:.3f}s", segment_id)
                except (RuntimeError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
                    _issue(report, "error", "segment_probe", str(exc), segment_id)

    if segments and _number(duration) and abs(previous_end - float(duration)) > 0.08:
        _issue(report, "error", "timeline_duration", f"Last segment ends at {previous_end:.3f}s but project duration is {float(duration):.3f}s")
    if premium:
        if not hero_scene_id:
            _issue(report, "error", "hero_scene", "editorial-premium requires project.hero_scene_id")
        elif hero_duration is None:
            _issue(report, "error", "hero_scene", f"hero_scene_id does not match a segment: {hero_scene_id}")
        elif hero_duration < 3.0:
            _issue(report, "error", "hero_scene", f"Hero scene is only {hero_duration:.2f}s; reserve enough time for a developed visual payoff", hero_scene_id)
    editorial_share = mode_seconds["editorial_collage"] / float(duration) if duration else 0.0
    if editorial_share > 0.35:
        _issue(report, "warning", "editorial_share", f"Editorial collage occupies {editorial_share:.0%}; default guidance is <= 30%")
    switches_per_minute = mode_switches / (float(duration) / 60) if duration else 0.0
    if switches_per_minute > 10:
        _issue(report, "warning", "mode_switch_density", f"{switches_per_minute:.1f} renderer switches/minute may feel visually fragmented")
    if premium and switches_per_minute > 6:
        _issue(report, "error", "premium_mode_switch_density", f"editorial-premium allows at most 6 renderer switches/minute; found {switches_per_minute:.1f}")
    report["metrics"] = {
        "segment_count": len(segments),
        "duration": duration,
        "mode_seconds": mode_seconds,
        "editorial_share": editorial_share,
        "mode_switches": mode_switches,
        "mode_switches_per_minute": switches_per_minute,
        "quality_profile": quality_profile,
        "hero_scene_id": hero_scene_id or None,
        "hero_scene_duration": hero_duration,
    }
    report["ok"] = not any(item["severity"] == "error" for item in report["issues"])
    return report


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--segments")
    parser.add_argument("--ledger")
    parser.add_argument("--verify-files", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    plan_path = Path(args.plan).expanduser().resolve()
    try:
        plan = _load_json(plan_path)
        plan_report = validate_plan(plan, Path(args.segments).expanduser().resolve() if args.segments else None)
    except (OSError, json.JSONDecodeError) as exc:
        plan_report = {"ok": False, "issues": [{"severity": "error", "code": "plan_read", "message": str(exc)}], "metrics": {}}
    report: dict[str, Any] = {"ok": plan_report["ok"], "plan": plan_report}
    if args.ledger:
        ledger_report = validate_ledger(args.ledger, args.verify_files)
        report["ledger"] = ledger_report
        report["ok"] = report["ok"] and ledger_report["ok"]
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
