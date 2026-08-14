---
name: rights-safe-media
description: Search, select, download, and audit rights-cleared stock footage or images for video script beats. Use when matching B-roll to narration, sourcing from Pexels, Pixabay, or Wikimedia Commons, handling local creator-owned media, creating attribution, or checking media license provenance.
---

# Rights-Safe Media

“Free,” “royalty-free,” and “public domain” are different. Keep the provider's actual license name and current license URL in the project ledger.

## Search workflow

1. Read the target segment from `video-plan.json`.
2. Convert abstract narration into observable subjects, actions, setting, era, and camera framing.
3. Create 2–5 short English queries. Add the central subject to every query, as MoneyPrinterTurbo does, but diversify the action and setting.
4. Call `mcp__knowledge_video_media__search_media` with the queries, orientation, and desired media type.
5. Inspect candidates for semantic fit, duration, resolution, orientation, visual continuity, and rights metadata.
6. Download only the selected candidate using `mcp__knowledge_video_media__download_media`.
7. Validate the ledger after each sourcing batch.

Do not download a candidate merely because it ranks first. Prefer a slightly less generic shot that literally supports the sentence.

## Query examples

| Narration | Weak | Better |
| --- | --- | --- |
| “信任正在下降” | `trust decline` | `empty town hall audience`, `customer reading contract carefully` |
| “供应链会放大波动” | `supply chain volatility` | `cargo containers delayed port`, `factory conveyor stopping` |
| “人们开始存钱” | `saving` | `hands putting coins savings jar`, `person writing monthly budget` |

Avoid value judgments, diagnoses, crimes, or political labels in searches for recognizable people. A generic person must not visually imply that they have a disease, committed a crime, or hold a sensitive belief.

## Provider policy

- Pexels: requires `PEXELS_API_KEY`; content uses the Pexels License. Keep the photographer/videographer and Pexels page URL.
- Pixabay: requires `PIXABAY_API_KEY`; content uses the Pixabay Content License. Keep the contributor and page URL.
- Wikimedia Commons: no API key; accept only machine-readable public-domain, CC0, CC BY, or CC BY-SA results by default. Preserve author and attribution text.
- Local media: record `provider: local`, the user's asserted rights basis, original path, and checksum. Treat an unsupported assertion as manual review.

Read `${CODEBUDDY_PLUGIN_ROOT}/skills/rights-safe-media/references/licensing-policy.md` before publication audit.

## Selection rules

- Prefer 1080p or better, with enough duration for the segment plus handles.
- Match the project orientation without destructive cropping of the subject.
- Reject watermarks, baked-in captions, logos used as decoration, and obvious AI artifacts unless intentionally disclosed.
- Avoid the same asset twice unless repetition is a deliberate motif.
- For historical claims, stock reenactment is not evidence. Use correctly labeled archival material or a clearly stylized animation.
- A provider license does not automatically clear trademarks, artwork, property, privacy, publicity, or moral rights.

## Ledger gate

Every external asset must have provider, provider asset ID, creator, source page, license name, license URL, retrieval time, local path, SHA-256, segment IDs, and attribution text. Missing any required field blocks publication.

Run:

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/media_cli.py" validate-ledger --ledger ./asset-ledger.json
```

The result is an operational audit, not legal advice.
