---
name: remotion-scenes
description: Create deterministic Remotion clips for knowledge videos from a routed segment plan. Use for parameterized charts, counters, UI walkthroughs, code animation, tables, kinetic type, precise numeric sequences, reusable templates, or aspect-ratio variants.
---

# Remotion Scenes

Use only for `remotion` segments or the overlay portion of `hybrid` segments. Keep exact timing from `video-plan.json`.

## Start from the bundled engine

Copy the JSON-driven starter without overwriting an existing scene:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/setup_remotion.py" \
  --output <scene-dir>
```

Write `<scene-dir>/public/segment.json`. The starter supports `kinetic-title`, `bar-chart`, `timeline`, `flow`, and `code` presets. Customize `src/Segment.jsx` when the plan needs a bespoke scene, but preserve frame determinism.

Install aligned packages:

```bash
cd <scene-dir> && npm install
```

## Authoring rules

- Use `useCurrentFrame()`, `interpolate()`, and `spring()` for time. Do not use timers, CSS animation, network calls during render, or unseeded randomness.
- Pass data through JSON or Remotion input props. Do not hard-code factual values that belong in the plan.
- Keep title-safe and caption-safe zones clear.
- Use a shared palette, type system, easing, and motion density from the project's `visual_system`.
- Label illustrative data as illustrative. Never invent source-backed charts.

## Inspect and render

Render a representative still before the full clip and inspect it:

```bash
npx remotion still src/index.jsx KnowledgeSegment audit/<segment-id>.png \
  --props public/segment.json --frame <hero-frame>
npx remotion render src/index.jsx KnowledgeSegment <segment.mp4> \
  --props public/segment.json
ffprobe -v error -show_format <segment.mp4>
```

The bundled composition calculates width, height, fps, and duration from the JSON props. Final output must match the plan exactly. Preserve the Remotion project under `scenes/`.

If Node/npm or Chromium cannot render, report a blocked segment with the exact command and error. Do not substitute a static screenshot while claiming the clip rendered.
