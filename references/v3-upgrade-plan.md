# V3 upgrade plan (written from the actual repository state, 2026-10-14)

## State audited before V3

| Area | State at V2 head (`2ee1b3e`) | Evidence |
|---|---|---|
| Rendering engines | 9: native whiteboard, handdrawn, motion, kinetic, artistic, image_whiteboard; adapters huashu_clip, animate_piece, html_seek | `scripts/studio_lib/engines/` |
| Styles | 19 registry entries, 18 verified operational (mg.liquid fails: WebGL renders black headless) | `styles/verification.json` |
| Storyboard | schema v2 with migrations; JSON + Markdown export | `schemas/project.schema.json`, `migrate.py` |
| Narration | SAPI with pause-anchored word alignment; edge (opt-in); file; estimate | `tts.py` |
| Shorts | native 9:16 recomposition, burned captions, CTA, parent map | `shorts.py` |
| SEO | metadata, chapter validation, thumbnail | `seo.py` |
| QA | probe, frame count, black/freeze, captions, richness, research gate, visual-review record | `qa.py` |
| Tests | 38 passing (core, render integration, V2) | `tests/` |
| Missing for V3 | niche research, audience profile, historical source tiers / claim classes, story architecture, maps, archival look, dubbing, analytics, unified voice engine | — |

## Plan
1. Audit the six V3 repos (5 cloned; 1 not found) → `references/v3-source-audit.md`.
2. `youtube_api.py`: a stdlib Data API + Analytics client with fixes over the upstream (median-baseline outliers, region targeting, quota budget, honest RPM).
3. `niche.py`: evidence ledger, transparent weighted scoring, confidence, a revenue-evidence category cap, a 30-episode roadmap and a 90-day calendar.
4. Real evidence collection, cited and dated (`examples/niche-research/`).
5. `audience.py`: a testable 50+ profile with WCAG contrast correction in the renderer.
6. `history.py`: source tiers, claim classes, ledger import and a fact-check report. `research.py` gains the contested and allegation statuses.
7. `story.py`: section budgets for 12–45 min formats and structure checks.
8. A `map` element (GeoJSON) and an `archival` engine.
9. `dubbing.py`: per-scene slot fitting, the shared M&E bed, exact-length tracks, localized SRT and metadata, QA, and an upload package. The YouTube API facts behind it were verified first.
10. `voice.py`: the unified provider layer (edge-tts / ElevenLabs MCP / SAPI / auto), caching, usage and quota guard.
11. `analytics.py`: Studio CSV and API ingestion, plus progress toward the US 55+ target.
12. Demo: the Ghost Army documentary (full render), 3 Shorts scripts, 1+ rendered Short, a Spanish dub sample, the SEO package, the publishing checklist and QA.
13. Tests, docs, and commit on `feature/youtube-animation-studio-v3`.
