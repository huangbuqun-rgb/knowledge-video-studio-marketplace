---
name: hyperframes-scenes
description: Author, validate, preview, and render HyperFrames segments for knowledge videos. Use for abstract concepts, causal systems, maps, diagrams, timelines, networks, equations, bespoke data stories, or hybrid explanatory overlays selected by a video plan.
---

# HyperFrames Scenes

Use only for segments routed to `hyperframes` or the overlay layer of `hybrid`. Keep timings from `video-plan.json`.

## Build

1. Group adjacent HyperFrames beats with the same visual system when practical.
2. Scaffold an agent-safe project:

```bash
HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes init <scene-dir> \
  --non-interactive --example blank --resolution <landscape|portrait|square>
```

3. Before hand-authoring a motion, search locally:

```bash
npx hyperframes catalog --query "<desired visual move>" --json
```

Do not enable the optional on-device semantic catalog silently; it downloads about 33 MB. Ask first.

4. Author the composition. The standalone root requires `data-composition-id`, `data-start="0"`, `data-width`, `data-height`, and exact `data-duration`. Every clip needs `data-start`, `data-duration`, and `data-track-index`. Register exactly one paused timeline under `window.__timelines[compositionId]`.

5. Keep rendering deterministic: no network fetches at render time, clocks, unseeded randomness, infinite loops, duplicate IDs, or CSS/GSAP transform conflicts. Put full-frame backgrounds on a full-bleed child, not on the composition root.

## Check and review

Run fast lint after the first structural pass, then the required final gate:

```bash
npx hyperframes lint <scene-dir>
npx hyperframes check <scene-dir> --snapshots --json
```

Inspect the generated snapshots. Add a `*.motion.json` sidecar for entrances, order, in-frame, and continued-motion assertions when the segment has meaningful motion.

After checks pass, start Studio preview and give the real project URL to the creator:

```bash
cd <scene-dir> && npx hyperframes preview --port <free-port>
```

The URL format is `http://localhost:<port>/#project/<directory-name>`. Keep the preview process alive. Obtain one approval for the complete HyperFrames group. Checks alone are not approval.

## Render after approval

```bash
npx hyperframes render <scene-dir> --quality high --output <segment.mp4>
test -s <segment.mp4>
ffprobe -v error -show_format <segment.mp4>
```

Render individual sub-compositions with `-c` when the group project contains multiple output segments. Copy or encode outputs to the exact project resolution, fps, and duration. Preserve the editable HyperFrames project under `scenes/`.

## Quality rules

- One sentence should produce one visual argument, not a slide full of prose.
- Use layout and motion to reveal relationships in narration order.
- Body text must fit without `<br>` hacks; captions belong in the global finishing pass.
- Do not use HyperFrames for generic decorative B-roll.
- If HyperFrames is unavailable, return a clear blocked status or explicitly reroute the segment to Remotion; never silently replace it with stock footage.
