#!/usr/bin/env python3
"""Run the measurable editorial-premium delivery checks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROFILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "knowledge-video-director"
    / "references"
    / "quality-profiles.json"
)


def _run(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _duration(path: Path) -> float:
    result = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)
    ])
    if result.returncode:
        raise RuntimeError((result.stderr or "ffprobe failed").strip())
    return float((_load_text_json(result.stdout).get("format") or {}).get("duration") or 0)


def _load_text_json(text: str) -> Any:
    return json.loads(text)


def _check(items: list[dict[str, Any]], name: str, ok: bool, severity: str, details: Any) -> None:
    items.append({"name": name, "ok": ok, "severity": severity, "details": details})


def _silences(path: Path) -> list[float]:
    result = _run([
        "ffmpeg", "-hide_banner", "-i", str(path), "-af",
        "silencedetect=noise=-42dB:d=0.4", "-f", "null", "-"
    ])
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return [float(value) for value in re.findall(r"silence_duration:\s*([0-9.]+)", output)]


def _volume(path: Path) -> dict[str, float | None]:
    result = _run([
        "ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a:0",
        "-af", "volumedetect", "-f", "null", "-"
    ])
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    mean = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", output)
    peak = re.search(r"max_volume:\s*(-?[0-9.]+) dB", output)
    return {
        "mean_db": float(mean.group(1)) if mean else None,
        "peak_db": float(peak.group(1)) if peak else None,
    }


def run_gate(plan_path: Path, narration: Path, final: Path, contact_sheet: Path | None) -> dict[str, Any]:
    plan = _load_json(plan_path)
    profiles = _load_json(PROFILE_PATH)
    project = plan.get("project") or {}
    profile_name = project.get("quality_profile", "standard")
    profile = profiles.get(profile_name) or profiles["standard"]
    checks: list[dict[str, Any]] = []

    planned_duration = float(project.get("duration") or 0)
    narration_duration = _duration(narration)
    final_duration = _duration(final)
    _check(
        checks,
        "final_duration",
        abs(final_duration - planned_duration) <= 0.15,
        "error",
        {"planned": planned_duration, "actual": final_duration},
    )
    _check(
        checks,
        "narration_fits_timeline",
        narration_duration <= planned_duration + 0.05,
        "error",
        {"narration": narration_duration, "timeline": planned_duration},
    )

    narration_text = "".join(str(item.get("narration") or "") for item in plan.get("segments", []))
    han_count = len(re.findall(r"[\u3400-\u9fff]", narration_text))
    chars_per_second = han_count / narration_duration if narration_duration else 0.0
    target_rate = (project.get("voice_strategy") or {}).get("target_chars_per_second")
    if not isinstance(target_rate, list) or len(target_rate) != 2:
        target_rate = profile.get("mandarin_chars_per_second", [4.2, 5.2])
    rate_ok = not str(project.get("language") or "").lower().startswith("zh") or (
        float(target_rate[0]) <= chars_per_second <= float(target_rate[1])
    )
    _check(
        checks,
        "narration_pace",
        rate_ok,
        "error",
        {"han_characters": han_count, "chars_per_second": round(chars_per_second, 3), "target": target_rate},
    )

    silence_values = _silences(narration)
    pause_limit = float(profile.get("ordinary_pause_max_seconds", 0.9))
    long_pauses = [round(value, 3) for value in silence_values if value > pause_limit]
    _check(
        checks,
        "ordinary_pauses",
        not long_pauses,
        "warning",
        {"limit_seconds": pause_limit, "long_pauses": long_pauses},
    )

    decode = _run(["ffmpeg", "-v", "error", "-i", str(final), "-f", "null", "-"], timeout=600)
    _check(checks, "full_decode", decode.returncode == 0, "error", (decode.stderr or "ok").strip())

    volume = _volume(final)
    peak = volume.get("peak_db")
    _check(
        checks,
        "audio_peak",
        peak is not None and peak <= -1.0,
        "error",
        {**volume, "maximum_allowed_db": -1.0},
    )

    if profile_name == "editorial-premium":
        sheet_ok = contact_sheet is not None and contact_sheet.is_file() and contact_sheet.stat().st_size >= 10_000
        _check(
            checks,
            "contact_sheet",
            sheet_ok,
            "error",
            {"path": str(contact_sheet) if contact_sheet else None, "minimum_bytes": 10_000},
        )

    score = 100
    for item in checks:
        if not item["ok"]:
            score -= 20 if item["severity"] == "error" else 5
    score = max(0, score)
    minimum = int(profile.get("minimum_compliance_score", 70))
    errors = [item for item in checks if not item["ok"] and item["severity"] == "error"]
    return {
        "ok": not errors and score >= minimum,
        "profile": profile_name,
        "score": score,
        "minimum_score": minimum,
        "checks": checks,
        "note": "This score covers measurable delivery compliance; the contact sheet still requires human visual judgment.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--narration", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--contact-sheet")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        report = run_gate(
            Path(args.plan).expanduser().resolve(),
            Path(args.narration).expanduser().resolve(),
            Path(args.final).expanduser().resolve(),
            Path(args.contact_sheet).expanduser().resolve() if args.contact_sheet else None,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report = {"ok": False, "error": str(exc)}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
