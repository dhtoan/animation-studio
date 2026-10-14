---
name: animation-studio
description: End-to-end animated YouTube production — research and fact ledger, retention-first script, storyboard, art direction, scene-level animation (whiteboard, hand-drawn, motion graphics, kinetic type, artistic, image-to-whiteboard, plus huashu/animate/lemo/dashi canvas adapters), narration with word-synced cues, captions, music/SFX mix, 16:9 long-form assembly, 9:16 Shorts recomposed (not cropped) and linked to the parent video, YouTube SEO package, and automated QA. Use when the user wants to plan, script, animate, render or package a YouTube video or Shorts, convert a long video into Shorts, or audit a video project's quality, timing, captions or rights.
---

# Animation Studio

A working pipeline, not a prompt pack. Everything below runs from `scripts/studio.py` (Python 3.10+, Pillow, numpy, ffmpeg).

## When this skill applies
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
| `html_seek` | seekable HTML pages: lemo-opuscar `render(t)`, dashi `seek(t)`, any `renderFrame(t)` page | [rendering](references/rendering.md) |

Cinematic transitions (from the video-shotcraft recipes): `crash_zoom`, `flash_cut`, `iris`, `blinds`, `glitch`, `light_leak`, plus cut, fade, crossfade, wipe, erase, push, whip, zoom_through and slide_up.

A style counts as **operational** only after `studio.py styles --verify` has rendered and validated a sample on this machine. Check `references/style-registry.md` before promising any look.

Each scene gets an explicit fallback chain. If an engine fails, the same elements are rendered by the fallback, so the facts on screen do not change.

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
- `references/source-audit.md` and `references/v2-source-audit.md`: what each upstream repo really does
- `styles/registry.json`: unified style registry; verification results live in `styles/verification.json`
- `tests/`: unit and integration tests (`python -m unittest discover -s tests`)
