---
name: knowledge-video-director
description: Turn a knowledge-creator script into a complete, coherent video production plan and route every beat to rights-cleared stock footage, HyperFrames, Remotion, editorial paper-collage animation, or a justified hybrid. Use for script-to-video, automatic B-roll matching, mixed motion design, knowledge explainers, and end-to-end video creation from narration or copy.
---

# Knowledge Video Director

Use `video-plan.json` as the only timing and routing source. Do not let individual renderers invent or change segment timings independently.

For full creation, default to `project.quality_profile: "editorial-premium"`. Use `standard` only when the creator explicitly asks for a fast draft. Premium is a production contract, not a style preset: it requires one continuous voice, one cross-scene visual anchor, one developed hero scene, evidence-role labeling, restrained audio, a contact sheet, and a measurable delivery gate.

## Step 1 — Resolve the source

Accept pasted text, Markdown, TXT, DOCX/PDF extraction, subtitles, or a narration audio transcript. Preserve the author's claims and wording unless they explicitly request script editing. Store the normalized source under `source/`.

If duration is unknown, estimate it from the actual narration when available; otherwise use the script's language-aware speaking rate and mark the duration as estimated. Default to 1920×1080, 30 fps, and the source language when platform and format are unspecified; state the assumption rather than blocking progress.

Unless the creator explicitly requests characters or multiple speakers, generate narration as one continuous take with one speaker, one voice profile, and one direction prompt. Never synthesize each visual beat with a separately randomized voice. For Mandarin explainers, target a natural conversational pace around 4.2–5.2 Chinese characters per second; avoid announcer delivery, drawn-out endings, and dramatic pauses between ordinary sentences. Record the reusable performance direction and rate target in `project.voice_strategy` before synthesis.

## Step 2 — Create the project

Create this structure without overwriting an existing project:

```text
source/  media/  scenes/  segments/  audit/  output/
```

Run:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/doctor.py"
```

Missing Pexels/Pixabay keys only disable those providers. Missing FFmpeg blocks assembly. Missing Node 22+ blocks HyperFrames and Remotion segments and must be surfaced before rendering.

## Step 3 — Split into semantic beats

Break the script at claim, example, contrast, causal step, data point, emotional turn, or chapter boundary. A beat should usually be 2–8 seconds. Do not cut solely on punctuation. Keep a complete spoken thought with the visual that explains it.

For each beat record:

- narration and semantic intent;
- start/end time;
- literal entities, actions, setting, data, and relationships;
- factual verification needs;
- evidence role: `evidence`, `context`, `mechanism`, `mood`, or `none`;
- one visual mode and a short reason;
- search queries or a renderer brief;
- transition and caption-safe constraints.

## Step 4 — Route the visuals

Read `${CODEBUDDY_PLUGIN_ROOT}/skills/knowledge-video-director/references/routing-policy.md` before choosing modes. Read `${CODEBUDDY_PLUGIN_ROOT}/skills/knowledge-video-director/references/video-plan.schema.json` before writing the plan.

Prefer one dominant visual language for a chapter. Define one reusable visual anchor—such as a window, map, timeline, diagram, or material surface—that can persist or transform across adjacent beats. For premium plans, write it to `visual_system.anchor`, copy its id to every segment's `visual_anchor_id`, and designate one `hero_scene_id`. The hero scene is the one moment where the explanatory mechanism receives enough time, layered motion, and visual detail to become memorable. Do not distribute equal decorative motion across every beat.

Do not alternate renderers every sentence. A renderer change is an implementation detail, not permission to introduce a new palette, type scale, framing system, or transition style. Premium plans may switch renderers at most six times per minute. Editorial collage should normally stay below 30% of total duration and should not be used as generic filler.

Write `video-plan.json`, then validate:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/validate_project.py" --plan ./video-plan.json
```

Fix every error before sourcing or rendering. Warnings require judgment but do not automatically block a planning-only request.

## Step 5 — Source stock and hybrid media

Invoke `rights-safe-media` only for `stock` and `hybrid` segments. Generate 2–5 concrete search phrases per segment. Search and inspect candidates, then download selected media only through `mcp__knowledge_video_media__download_media`, which writes the license ledger.

Never use Google Images, social-media reposts, or a direct file URL with unknown provenance. Local user media must still receive a ledger entry identifying it as user-supplied and noting the user's asserted rights basis.

## Step 6 — Render motion segments

Invoke the matching skill:

| Mode | Skill | Typical output |
| --- | --- | --- |
| `hyperframes` | `hyperframes-scenes` | diagrams, maps, systems, conceptual explanation |
| `remotion` | `remotion-scenes` | charts, UI, code, precise numbers, reusable parameterized motion |
| `editorial_collage` | `editorial-collage-scenes` | hook, contrast, historical turn, editorial metaphor |
| `hybrid` | media skill plus one renderer | footage with explanatory overlays |

All clips must match the plan's width, height, fps, and exact segment duration. Put final segment clips at `segments/<segment-id>.mp4` and metadata beside them at `segments/<segment-id>.json`.

When adjacent beats share a visual anchor, prefer one continuous master composition and use stock images as layers inside it. Avoid assembling self-contained title cards that read like unrelated slides. Use a match cut or continuous transformation when the same idea changes state.

HyperFrames is the exception to unattended final rendering: after `check` passes, start Studio preview and obtain one final approval before high-quality render. This is a single project-level checkpoint, not a per-segment interruption.

## Step 7 — Assemble and caption

Invoke `video-finisher`. Use narration as the timing authority. Keep important graphics outside the caption-safe band. Assemble only after every planned segment exists and passes ffprobe checks.

For premium plans, write `project.audio_strategy` before mixing. Default to narration at -16 LUFS, music at least 18 dB below narration, no more than three semantic sound effects per 40 seconds, and `--bgm-volume 0.06`. Always create a voice-only comparison render when music or effects are used.

## Step 8 — Audit and hand off

Run:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/validate_project.py" \
  --plan ./video-plan.json \
  --ledger ./asset-ledger.json \
  --segments ./segments

python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/quality_gate.py" \
  --plan ./video-plan.json \
  --narration ./source/narration.wav \
  --final ./output/final.mp4 \
  --contact-sheet ./audit/contact-sheet.jpg \
  --output ./audit/quality-report.json
```

Deliver the final MP4 together with `video-plan.json`, `asset-ledger.json`, attribution text, and an audit summary. Say “publish-ready” only when there are no blockers. Explain that the audit is operational guidance, not legal advice.

## Non-negotiable quality rules

- Visuals explain the sentence; they do not merely repeat it as text.
- Keep one coherent visual anchor across adjacent beats; do not expose renderer names, tool labels, fake app chrome, decorative progress bars, or template UI unless the content requires them.
- Use one continuous voice by default. Multiple voices, character acting, or per-section speaker changes require an explicit creator request.
- Premium plans require one developed hero scene; do not spend the animation budget evenly on decorative transitions.
- Label footage by evidence role. Historical evidence must be the claimed subject and date/context, not generic aviation, office, city, or technology imagery.
- Treat the contact sheet as one visual system. An automated score cannot replace the final human judgment of hierarchy, continuity, and taste.
- Stock footage must be concrete and semantically relevant, not mood-only filler.
- Do not fabricate charts, quotations, interfaces, maps, or historical documents.
- Do not use official Vox logos, nameplates, or claim affiliation; “editorial paper-collage” is a style description only.
- Keep source pages and license URLs. A downloaded file without provenance is not usable.
- Preserve creator-editable project files for every generated animation.
