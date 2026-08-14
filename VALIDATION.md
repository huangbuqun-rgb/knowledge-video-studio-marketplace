# Validation report

Validated on macOS with WorkBuddy 5.3.11; public 1.1.0 checks refreshed on 2026-08-14.

## Passed

- WorkBuddy bundled CLI plugin manifest validation.
- WorkBuddy bundled CLI marketplace manifest validation.
- WorkBuddy `quick_validate.py` for all six skills.
- Python compilation and JSON parsing for every bundled script and manifest.
- MCP `initialize`, `tools/list`, and `tools/call` over stdio.
- Live Wikimedia Commons search with automatic license filtering.
- Live CC0 image download, atomic `asset-ledger.json` write, SHA-256 verification, and stable-source validation.
- Remotion dependency installation, React bundle, still render, and MP4 render.
- HyperFrames 0.7.107 non-interactive scaffold and full `check` gate with zero findings.
- FFmpeg editorial-poster animation, segment ffprobe validation, timeline normalization, concatenation, and final MP4 verification.
- Editorial Premium plan enforcement: one-take voice strategy, visual anchor, hero scene, evidence roles, restrained audio plan and renderer-switch ceiling.
- Measurable quality gate: narration pace and pause analysis, full decode, duration, audio peak and contact-sheet presence.

## Environment observed

- Python 3.9.6
- FFmpeg 6.0
- ffprobe 4.4
- Node.js 24.17.0
- npm/npx 11.13.0

## Not exercised

Pexels and Pixabay live API calls were not exercised because no API keys were present. Their absence was correctly reported without exposing environment values, and auto mode fell back to Wikimedia Commons. Their endpoints and result parsers follow the current official API documentation linked in the plugin's `references/upstream.md`.
