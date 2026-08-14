---
name: editorial-collage-scenes
description: Create original editorial paper-collage animation segments for knowledge videos. Use for a strong hook, chapter turn, historical or cultural contrast, conflict, editorial metaphor, or stylized connector beat selected by the script-driven visual plan.
---

# Editorial Collage Scenes

This is an original editorial paper-collage workflow, not an official Vox product or brand imitation. Never use Vox logos, nameplates, signature lower-thirds, or imply affiliation.

## When to use

Use for `editorial_collage` segments and only when the beat benefits from compression, contrast, or metaphor. Keep the mode under roughly 30% of total duration unless the creator explicitly chooses an all-collage direction.

## Local workflow

1. Turn the segment into 2–4 visual layers: background texture, one dominant subject, supporting cutouts/documents, and code-rendered type or arrows.
2. Source every documentary element through `rights-safe-media`, or generate original elements with the available WorkBuddy image-generation capability. Generated imagery that resembles evidence must be visibly stylized and disclosed.
3. Generate a clean poster frame at the final aspect ratio. Avoid long AI-rendered text; add factual text later in code.
4. Save the poster and separate layers under `scenes/<segment-id>/assets/`.
5. Animate a flat poster with the bundled helper when layered animation is not necessary:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/animate_collage.py" \
  --input <poster.png> --output <segment.mp4> \
  --duration <seconds> --width <width> --height <height> --fps <fps> \
  --motion push-in
```

For layered scenes, author the motion in Remotion or HyperFrames but keep the segment's route `editorial_collage` and preserve the collage art direction.

## Art direction

- Build one dominant visual metaphor per beat.
- Use torn-paper masks, photocopy grain, halftone, redaction bars, map fragments, and physical depth selectively.
- Keep the factual hierarchy legible: headline, evidence, implication.
- Use fast entrances and restrained hold motion; avoid constant decorative jitter.
- Avoid close copies of a living publisher's branded compositions.

## Verification

Inspect the opening, midpoint, and final frame. Confirm no generated faces, documents, maps, dates, or quotations could be mistaken for authentic evidence. Write a segment metadata JSON listing every external source and whether each element is generated, licensed, or user-supplied.
