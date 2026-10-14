---
name: animation-studio
description: End-to-end animated YouTube production, including evidence-based niche research for U.S. 50+ documentary channels, historical fact-checking, documentary story architecture, multilingual dubbing (one video, several audio tracks) and an analytics learning loop — research and fact ledger, retention-first script, storyboard, art direction, scene-level animation (whiteboard, hand-drawn, motion graphics, kinetic type, artistic, image-to-whiteboard, plus huashu/animate/lemo/dashi canvas adapters), narration with word-synced cues, captions, music/SFX mix, 16:9 long-form assembly, 9:16 Shorts recomposed (not cropped) and linked to the parent video, YouTube SEO package, and automated QA. Use when the user wants to plan, script, animate, render or package a YouTube video or Shorts, convert a long video into Shorts, or audit a video project's quality, timing, captions or rights.
---

# Animation Studio

A working pipeline, not a prompt pack. Everything below runs from `scripts/studio.py` (Python 3.10+, Pillow, numpy, ffmpeg).

## When this skill applies
- Find and rank documentary niches and topics for a channel, especially one serving U.S. viewers 50+. Every signal must be cited, and RPM is never invented.
- Research and fact-check a historical documentary. Write a 12–45 minute script with chapters, sources and stated uncertainty.
- Produce dubbed audio tracks, localized subtitles and metadata for one master video.
- Analyse channel performance from YouTube Analytics (when authorised) or Studio CSV exports.
- Make or plan a YouTube explainer, documentary or deep dive (8–30 min) or a custom length.
- Turn a topic or script into a storyboard and rendered animation.
- Produce Shorts from a long video, with a mapping to the parent video.
- Generate YouTube metadata (titles, description with chapters, tags, pinned comment, thumbnail).
- QA a render: resolution, duration, fps, black or frozen frames, captions, missing assets, rights.

## Operating procedure
1. **Check the machine**: `python scripts/studio.py capabilities` shows which engines, TTS providers, ffmpeg and fonts exist. Never promise an engine or voice that isn't listed `ok`.
2. **Research first** ([research](references/research-and-fact-checking.md)):
   - Fill `research/brief.md`.
   - Record every factual claim in `research/facts.json` with a status: `verified`, `hypothesis`, `fictional`, `illustrative` or `unverified`.
   - Use a fictional company or case when claims cannot be verified. Business and scandal topics get the [extra gate](references/copyright-and-licensing.md#reputational-risk).
3. **Script** ([scriptwriting](references/scriptwriting.md), [retention](references/long-form-retention.md)):
   - Hook, viewer promise, central question, developments, answer, then a next-video bridge.
   - Budget about 130 spoken words per minute at SAPI rate −1, and 150 wpm for typical human voice-over.
4. **Storyboard as `project.json`** ([storyboarding](references/storyboarding.md), schema at `schemas/project.schema.json`):
   - One scene per narrative beat.
   - Every scene has narration, purpose, visual, camera, transition and elements.
   - Element timing uses `"cue:word"` so motion lands on the spoken word.
5. **Art direction and shot planning** ([art direction](references/art-direction.md), [shot planning](references/shot-planning.md), [style registry](references/style-registry.md), [image art direction](references/image-art-direction.md)):
   - Set `art_style` on scenes to a registry id (`studio.py styles` lists them with verified status). The engine and default params are then filled automatically.
   - `studio.py direction <slug>` prints the style bible, the auto-filled shot plan, continuity issues, and a 1 + 2 style proposal drawn only from styles verified on this machine.
   - Pick a theme and the engine per scene, either explicitly or with `engine: "auto"` (router).
   - Keep the palette meaning fixed: amber = attention, red = loss, green = growth.
6. **Validate and dry-run**: `studio.py validate <slug>`, then `studio.py dry-run <slug>`. Fix every error; read every warning.
7. **Preview stills** before rendering video: `studio.py preview <slug> --scene s05`. Look at them (Read the PNGs).
8. **Build**:
   - `studio.py build <slug> --quality draft` to review, then `--quality final` (1920×1080, 30 fps).
   - Builds are cached per scene and resumable. Re-running only renders changed scenes.
   - Use `--fit` only to pad visual holds when the narration is already final.
9. **Shorts** ([shorts](references/shorts-conversion.md)):
   - Add `shorts[]` to the project, then run `studio.py shorts <slug>`.
   - Shorts are native 9:16 re-renders with burned captions and a CTA, mapped to the parent chapter and timestamps.
10. **SEO** ([YouTube SEO](references/youtube-seo.md)): `studio.py seo <slug>`.
11. **QA** ([quality assurance](references/quality-assurance.md)):
    - Run `studio.py qa <slug>`, open the contact sheets in `previews/`, review them, then run `studio.py review <slug> --approve --notes "..."`.
    - Only call a deliverable done when `reports/quality-report.json` marks it OK.
12. **Report honestly**: what rendered, what is placeholder (for example the `estimate` voice), what is blocked.

## Documentary workflow (V3)
Niche research → opportunity scoring → topic → historical research → fact-check → script → storyboard → art direction → render → English narration → master → dubbing → Shorts → SEO → publishing checklist → analytics.

| step | command | reference |
|---|---|---|
| niche evidence + ranking + 30-episode roadmap | `studio.py niche score --dir research/niche` (`niche collect --query …` with `YT_API_KEY`) | [niche intelligence](references/niche-intelligence.md) |
| dossier → claims ledger, fact-check report | `studio.py history <slug> import --dossier …` / `history <slug> report` | [documentary production](references/documentary-production.md) |
| structure and word budgets / script check | `studio.py story plan --minutes 18` / `story check <slug>` | same |
| 50+ presentation audit (pace, contrast, text size) | `studio.py audience <slug>` | same |
| dubbing (one video, many audio tracks) | `studio.py dub <slug> --lang es,de` | [multilingual dubbing](references/multilingual-dubbing.md) |
| voice providers | `studio.py voice status|list|sample|jobs|ingest|verify-elevenlabs` | [voice engine](references/voice-engine.md) |
| performance loop | `studio.py analytics --exports analytics/exports` | [YouTube API notes](references/youtube-api-notes.md) |

Rules specific to V3:
- **RPM.** RPM is creator revenue per 1,000 views; CPM is advertiser cost. Never infer another channel's RPM. Revenue appears only as an evidence *category*, unless it was measured in your own Analytics.
- **Audience scope.** The audience goal is a target, never a promise. Analytics has no 50+ age bucket, so measure age55-64 plus age65-.
- **Historical claims** are classed as established, contested, allegation, reconstruction or fictional. Contested claims are framed on screen. Recreations carry an "ILLUSTRATIVE RECREATION" label (the `archival` engine).
- **ElevenLabs** goes through the agent-delegated MCP flow. It is used only after `voice verify-elevenlabs` succeeds **and** the project sets `voice.elevenlabs.approved`. Never claim it is connected otherwise.
- **Uploads.** The Data API cannot upload audio tracks, so we prepare Studio-ready files plus `reports/publishing-checklist.md` and never upload.

## Engines (details: [rendering](references/rendering.md))

| Engine | Best for | Reference |
|---|---|---|
| `whiteboard` | processes, cause→effect, teaching | [whiteboard](references/whiteboard-animation.md) |
| `handdrawn` | story beats, characters, reveals | [hand-drawn](references/hand-drawn-animation.md) |
| `motion` | charts, counters, networks, comparisons | [motion graphics](references/motion-graphics.md) |
| `kinetic` | hooks, quotes, punchlines (word-synced) | [motion graphics](references/motion-graphics.md) |
| `artistic` | atmosphere, metaphor, chapter openers | [art direction](references/art-direction.md) |
| `image_whiteboard` | draw a supplied illustration stroke by stroke | [whiteboard](references/whiteboard-animation.md) |
| `huashu_clip` | huashu-art-motion grammars (finance chart, 3b1b, Vox…) | [rendering](references/rendering.md) |
| `animate_piece` | cth9191/animate pieces (cut-paper, riso…) | [rendering](references/rendering.md) |
| `archival` | labelled historical recreations: sepia, flicker, typewriter type | [documentary production](references/documentary-production.md) |
| `html_seek` | seekable HTML pages: lemo-opuscar `render(t)`, dashi `seek(t)`, any `renderFrame(t)` page | [rendering](references/rendering.md) |
| `sweety_draw` | an illustration drawn part by part with pen lifts, then brush-painted (vendored sweety-handdraw-video) | [visual-fidelity audit](references/visual-fidelity-audit.md) |

### Premium documentary look (visual-fidelity upgrade)
Set `"quality_profile": "documentary-premium"` and give scenes a `look` from `styles/design-system.json`:
- `historical-illustrated`: an animate crosshatch piece
- `kinetic-type`: huashu y5
- `data-editorial`: huashu t3
- `premium-whiteboard`: lemo wb.js
- `technical-blueprint`: lemo blueprint
- `military-map`: mg-style d3 map
- `hand-drawn-illustration`: sweety_draw
- `archival-press`

Every look runs an upstream repository's own renderer, verified against its native output; see [the audit](references/visual-fidelity-audit.md).

In premium projects:
- **Engines.** Native Pillow engines are refused, and fallbacks never degrade to them. A missing dependency raises `EngineUnavailable`, which names it. A scene may opt out only with `allow_native` and a stated `native_reason`.
- **Multi-scene pieces.** A piece such as a crosshatch film or a lemo page can draw several scenes. Mark those scenes `params.era: true`. The pipeline lays the eras out from the real narration timing (`piece_timing.py`). Morph bridges run only between adjacent scenes.
- **Visual QA.** `visual_qa.run_visual_qa` checks each scene for blank composition, static scenes, edge clipping, balance, aspect, silent fallback, primitive engines, degraded dependencies, overflow, typography and continuity. In premium projects these are blockers.
- **Fonts.** Run `python scripts/fetch_fonts.py` once to restore the OFL fonts that lemo pages request. Its `--check` flag verifies them.

Cinematic transitions (from the video-shotcraft recipes): `crash_zoom`, `flash_cut`, `iris`, `blinds`, `glitch`, `light_leak`, plus cut, fade, crossfade, wipe, erase, push, whip, zoom_through and slide_up.

A style counts as **operational** only after `studio.py styles --verify` has rendered and validated a sample on this machine. Check `references/style-registry.md` before promising any look.

Each scene gets an explicit fallback chain. If an engine fails, the same elements are rendered by the fallback, so the facts on screen do not change. Premium projects are the exception: their chain contains only authentic engines.

## Hard rules
- No fabricated quotes, statistics or allegations. Use the claims ledger, and on-screen "FICTIONAL / ILLUSTRATIVE" badges where they apply.
- No third-party characters, footage or art without a licence record. Every asset needs `license` in the spec.
- Do not call paid APIs, upload or publish without the user's explicit approval. The `edge` TTS sends text online and is opt-in (`voice.allow_network`).
- Never claim views, virality or growth outcomes.
- Report actual test and render results only.

## Files
- `scripts/`: CLI and `studio_lib/` (engines, router, TTS, timeline, audio, render, shorts, SEO, QA)
- `adapters/vendor/`: vendored upstream code with licences
- `schemas/`: JSON schemas
- `templates/`: project and research templates
- `agents/`: sub-agent briefs (researcher, scriptwriter, storyboard artist, QA reviewer)
- `examples/billion-dollar-collapse/`: complete demo
- `references/source-audit.md`, `references/v2-source-audit.md` and `references/v3-source-audit.md`: what each upstream repo really does
- `examples/ghost-army/`: V3 historical documentary demo (dossier with 60 sourced claims, 45 scenes, Spanish dub sample). Scenes g01–g19 are rebuilt with the premium looks; the pieces are in `examples/ghost-army/pieces/`.
- `styles/design-system.json`: documentary design system (palettes, colour semantics, typography roles, motion and layout rules, looks)
- `examples/niche-research/`: cited evidence ledger (159 items), 20 scored ideas, 30-episode roadmap
- `styles/registry.json`: unified style registry; verification results live in `styles/verification.json`
- `tests/`: unit and integration tests (`python -m unittest discover -s tests`)
