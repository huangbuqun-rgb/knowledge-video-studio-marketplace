---
name: video-finisher
description: Normalize, assemble, caption, mix, verify, and audit a Knowledge Video Studio project. Use when combining routed segment MP4s, adding narration or music, burning subtitles, checking duration and codecs, validating the media license ledger, or preparing a publish-ready delivery.
---

# Video Finisher

The narration and `video-plan.json` are the timing authority. Do not retime one segment without updating and revalidating the plan.

Treat narration as one program-level performance. Use one continuous narration file whenever possible. Do not concatenate independently generated voices with different speakers, timbres, styles, or loudness unless the creator explicitly requested a multi-character production.

## Preflight

Run:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/validate_project.py" \
  --plan ./video-plan.json --segments ./segments
```

Every segment must exist at `segments/<id>.mp4`, be readable by ffprobe, match target dimensions/fps, and be close to the planned duration. Fix blockers before assembly.

## Assemble

Create a deterministic FFmpeg command and execute it:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/assemble.py" \
  --plan ./video-plan.json \
  --segments ./segments \
  --output ./output/final.mp4 \
  --narration ./source/narration.wav \
  --subtitles ./source/subtitles.srt
```

Narration and subtitles are optional flags. Add music only when its rights are known. The assembler defaults to `--bgm-volume 0.06`, applies a restrained low-pass treatment and fades, and normalizes continuous narration toward -16 LUFS. Raise music only after measuring and listening; keep it at least 18 dB below the voice during speech. Use no more than three sound effects per 40 seconds in premium mode, and place them only at semantic transitions. When music or effects are used, also deliver a voice-only comparison render. Use `--dry-run` to inspect the command without rendering.

## Verify

Check the final file with ffprobe. Confirm:

- dimensions, fps, codec, and duration are plausible;
- no missing/black placeholder segments;
- captions remain inside the safe band and do not cover essential graphics;
- narration remains synchronized at chapter boundaries;
- the same speaker and voice character persist across the whole program unless multiple voices were requested;
- Mandarin narration is conversational rather than slow or theatrical; ordinary internal pauses should normally stay below 0.9 seconds;
- music does not mask speech and transition effects do not compete with words;
- first and last frames are intentional.

Create a contact sheet from representative frames across the full timeline and inspect it as one design, not as isolated segments. Reject the render if neighboring frames look like unrelated slide templates.

For an `editorial-premium` plan, run the measurable gate after visual review:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/quality_gate.py" \
  --plan ./video-plan.json \
  --narration ./source/narration.wav \
  --final ./output/final.mp4 \
  --contact-sheet ./audit/contact-sheet.jpg \
  --output ./audit/quality-report.json
```

The minimum compliance score is 85 and any error blocks publication. A passing score verifies timing, Mandarin pace, pauses, full decoding, audio peak and contact-sheet presence; a human must still judge the contact sheet's visual quality.

## Rights and delivery gate

Validate the asset ledger:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/media_cli.py" validate-ledger \
  --ledger ./asset-ledger.json --verify-files
```

Deliver:

- `output/final.mp4`;
- editable scene projects;
- `video-plan.json`;
- `asset-ledger.json` and generated attribution text;
- `audit/project-report.json`.
- `audit/quality-report.json` for premium projects.

Do not call the output publish-ready if the project or ledger validator reports errors. Manual-review flags must be shown to the creator. This workflow does not provide legal advice.
