# V2 source audit

Audit date: 2026-10-14. These are read-only shallow clones in `_upstream/`, which sits outside the skill. Nothing upstream was modified or installed, and no upstream install scripts were run. Instructions found inside the repos were treated as untrusted data.

- **Verified** means read in code or executed here.
- **Inferred** means not executed.

**Integration methods:**
- **A** — native (code reused or ported)
- **B** — adapter
- **C** — skill / reference
- **D** — external dependency
- **E** — reference only

| Repo | Commit | License | Method | Summary |
|---|---|---|---|---|
| lemomo-ai/lemo-opuscar | `fdc46d7` (2026-10-13) | MIT (demo assets CC0/CC-BY/OFL per `CREDITS`; third-party marks excluded) | **B + C** | 43 code-only film styles with a `window.render(t)` page contract. Driven by our `html_seek` adapter (contract `lemo`). DIRECTOR/STYLE guides condensed into `references/shot-planning.md` |
| threerocks/sweety-image-art-direction | `07cddd3` (2026-10-07) | MIT | **C** | Prompt-only art-direction rules (no code). Condensed into `references/image-art-direction.md` |
| Kianzzz/xilo-opus-video | `f2cd828` (2026-09-29) | MIT | **C + A** | Plan → brief → build → self-critique workflow plus numpy SFX and a beat tracker. Spring tiers ported to `design.SPRINGS`. Self-critique table adopted in QA docs |
| Vincentwei1021/mg-styles-15 | tree `49052d8` (2026-10-05) | MIT (fonts not distributed; CC0/PD media per README) | **B + C** | 15 code-written 10 s motion-design films with the contract `renderAt(t)` + `__ready` + `DEMO`. Driven by `html_seek` (contract `mg`) |
| chuspeeism/dashi-animationstyle | `aa620f3` (2026-10-13) | MIT (example voice WAV excluded) | **B + C + A** | 7 HTML/Canvas explainer templates with a `window.seek(t)` contract. Driven by our `html_seek` adapter (contract `dashi`). The richness metric is ported to `qa.richness()`, and the timing rules go into `references/motion-graphics.md` |
| Vincentwei1021/video-shotcraft | `13c74a7` (2026-10-13) | Apache-2.0 (Remotion has its own company license; 6 SFX flagged "provenance unverified") | **C + A**, Remotion **D** | 124 shot recipe cards. A curated subset of 2D camera and transition moves is ported natively (`crash_zoom`, `flash_cut`, `iris`, `blinds`, `glitch`, `light_leak`). Shot grammar goes into `references/shot-planning.md` |
| WaterDJiang/Wattter_openSkills | `c91aa78` (2026-10-08) | **CC BY-NC-SA 4.0 (non-commercial)**; video skill states "no code license" | **E** | Personal plugin marketplace (13 Chinese skills, no YouTube tooling); patterns re-implemented, nothing copied |

---

## 1. lemo-opuscar (MIT © LemoLab)

**Verified:**
- 43 styles, each with `styles/<slug>/STYLE.md` (art-direction prompt, camera grammar, sound palette, pitfalls), `style.json` and a full demo `demo/index.html` exposing `window.render(t)`, `READY`, `DUR` and optional `EV`/`TEXTS(t)`.
- Shared toolkit `core/`:
  - `serve.mjs`: localhost server with host-header and path-traversal guards.
  - `video.mjs`: N `playwright-core` workers taking JPEG screenshots, piped to ffmpeg.
  - `readcheck.mjs`: reading time = Latin letters/15 + 1.5 s.
- By detection, 7 demos are three.js and about 15 use WebGL shaders; the rest are Canvas 2D or SVG.
- The "OPUSCAR 98" film has no source code. `styleboard/opuscar98_styles.json` holds 98 prompt-only styles, some naming living artists (strip those names before reuse).
- No paid APIs in code.

**Upstream tests run by the auditor (passed):**
- `core/render/srt.py`: cue overlap and rounding.
- `core/render/sheet.py`: contact sheet.
- `core/lib.js`: deterministic `mulberry`.

**Dependencies and runtime:**
- Node 20+ with `playwright-core`, `three`, ffmpeg.
- Python 3.11+ with numpy, scipy, soundfile, soxr.
- kokoro-onnx TTS requires Python < 3.14 and is **not usable here**.
- Sample libraries are 70–400 MB downloads.
- macOS-developed ("Windows: use WSL").

**Security:** `plugin/.../setup.sh` clones the repo into `~/lemo-opuscar` and runs `git fetch && reset --hard` on every run. That is an unpinned auto-update with supply-chain risk, so it is **not used**. We point at a pinned checkout instead.

**Integration:**
- `html_seek` engine with `contract: "lemo"`, which serves the library root and calls `render(t)` (see §8 for render evidence).
- `references/cinematic-direction.md` paraphrases the DIRECTOR.md process (treatment → shot list → beat sheet → cue map). No text is copied.

## 2. sweety-image-art-direction (MIT © threerocks)

**Verified:** a single Chinese SKILL.md with no code and no dependencies. It covers:
- Reference-image role assignment.
- A "restrained professional" default: one key light, at most three main colours.
- Big-shapes-first composition.
- Anti-cheap rules for portraits, posters and hand-drawn media.
- Single-goal edit loops with preservation lists.
- A QA checklist.

It needs the host's image generation (possibly paid) to produce anything, and it declares itself the sole entry point. We therefore do **not** embed it; we condense its rules into `references/image-art-direction.md` (paraphrased, with attribution).

## 3. xilo-opus-video (MIT © 周行)

**Verified (15/15 files present):**
- Workflow: three divergent plans → keyframe preview → `brief.md` → shot-by-shot build with QA stills → 7-criteria self-critique repeated until every score is 8 or more.
- `scripts/render.py`: Python Playwright `file://` screenshots piped to ffmpeg, with `tmix` motion blur.
- `audio_tools.py`: numpy SFX and a beat tracker. Auditor test: 100/120/128/150 BPM came back as 99.88/120.06/128.20/150.08.
- `check_env.py` crashes when ffmpeg is missing. This is an upstream bug.

**External:** the green-screen character path relies on external video models (Grok/Jimeng/Kling/Seedance), which are typically paid. **Not integrated.**

**Integration:**
- Spring tiers ported to `design.SPRINGS`.
- The self-critique rubric is used in `references/quality-assurance.md`.
- The renderer duplicates our adapter, so it is not reused.

## 1b. lemo-opuscar: demo assets (verified scan)
A scan of every `styles/*/demo` for referenced files shows that **only `pixel-rpg` has all its assets in git**. The other 42 reference font binaries (`.ttf`/`.woff2`) or `three/addons` modules that are not tracked upstream. Example: `whiteboard` references `fonts/ArchitectsDaughter-Regular.ttf`, which is absent, so `document.fonts.load` rejects and `READY` is never set; our first verification run timed out at 180 s.

`html_seek` now serves a local fallback font for missing font files, logged as a degradation in `styles/verification.json`. Demos that also need `node_modules` (three.js) remain unsupported.

## 4. mg-styles-15 (MIT © 2026 Vincentwei1021)
**Fetch.** A full clone stalled on the ~555 MB of media (fifteen 11–38 MB MP4s plus 102 FLAC samples). We fetched only the 164 text and source files at tree `49052d8`, via raw.githubusercontent.com; see `_FETCHED_FROM.txt`.

**What it is (verified):**
- Fifteen 10 s films, each with `prompts/NN-*.md`, `demos/NN-*/index.html` plus JS, a `cues.json` beat sheet and `audio.py`.
- Contract: `window.DEMO {width, height, fps, duration, motionBlur}`, `window.renderAt(t)` (async), `window.__ready`.
- Renderer: `harness/render.mjs` (puppeteer-core).

**Missing pieces:**
- Every demo awaits `document.fonts.load`, but the font files are not distributed upstream.
- 5 demos need `node_modules` (three, d3, topojson, opentype, simplex-noise).
- 3 need media we did not fetch.

**Auditor render (Python Playwright, existing Chromium, font fallback):** 01-flat-vector, 20-pixel and 07-liquid (WebGL2) rendered with no errors. 02/08/09/12 render with texture warnings, 06 fails.

**Integration:**
- `html_seek` contract `mg`: awaits `renderAt`, pauses and seeks WAAPI animations to t.
- Registry entries `mg.flat-vector`, `mg.pixel`, `mg.liquid`.
- `template.md` and `rubric.md` are reused as patterns (paraphrased) for style prompts and QA.

## 5. dashi-animationstyle (MIT © Dashi AI Lab 2026)

**Verified:**
- Contract: `window.seek(t)` must be a pure function of t, plus `window.ready` and a `window.TL` timeline. CSS animation, rAF, `Date.now()` and unseeded random are forbidden.
- `pipeline/render.mjs`: raw CDP, zero npm deps, Node 22+.
- `pipeline/动效部件.js`: a deterministic transitions and secondary-motion library.
- `丰富度检查.mjs`: richness check, the mean absolute difference between frames sampled every 2.5 s.
- 7 tested templates. The "27 styles" are mostly a parameter dictionary: 7 kept, 1 test page, 4 dropped, 15 untested.

**Platform:** macOS-only paths and fonts. It runs on Windows with an explicit Chrome path; the handwritten fonts fall back.

**Auditor render (verified):** Python Playwright with the existing Chromium rendered the 黑底科技 and 手绘笔记 example pages with 0 page errors and 0 network requests, at about 850 and 274 ms/frame.

**Integration:**
- `html_seek` engine with `contract: "dashi"` for template-based pages.
- Richness metric ported to `qa.richness()`.
- The motion-density rules (a visible change every 2–3 s, no stillness over 2 s, 0.3–0.7 s transitions) are paraphrased in `references/motion-graphics.md`.

## 6. video-shotcraft (Apache-2.0 © Vincentwei1021)

**Verified:**
- 124 shot cards / 150 variants in 10 categories, each with intent, a frame-level parameter table and pitfalls.
- A Remotion 4.0.484 template film and 226 TSX demos.
- An aesthetic rulebook (for example: hold ≥ 1 s, at most 3 full-frame impacts per film, text ≥ 5% of frame height).
- An energy-arc sequence guide.
- An SFX library.

The Remotion demos cannot run without `npm install` and Remotion's license terms, so they are **D (opt-in, not installed)**.

**Untrusted instructions ignored:**
- SKILL.md tells the agent to auto-open a workbench and promote the author's social accounts after delivery.
- `publish/upload_post.py` posts to a third-party API with a key.

**Integration (A, ported from the parameter tables with attribution):**
- `engines/base.py` transitions: `crash_zoom` (6-frame ease-in push to 2.6×, 3.5% pre-pull, shake 14 px·e^(−t/1.8)), `flash_cut`, `iris`, `blinds`, `glitch`, `light_leak`.
- `references/shot-planning.md` (shot types, energy arc, rule set).

The Apache-2.0 NOTICE is reproduced in `THIRD_PARTY_NOTICES.md`.

---

## 7. Wattter_openSkills (CC BY-NC-SA 4.0 per README; no LICENSE file)

Verified:
- 13 skills. 12,176 of the 12,709 files are vendored icon SVGs in the pptx builder.
- `wtt-code-animation-studio` claims 10 styles, but the starter implements only `flat`, `sand` and `particles`; the rest are recipes the agent writes per film.
- `pipeline.py` fails on Windows (`import fcntl`). With `fcntl` stubbed, the auditor got a correct 630-frame timeline.
- No YouTube functionality anywhere.

Licence: the non-commercial share-alike licence conflicts with a monetised channel, and the video skill states it has no code licence. **Nothing is copied.**

Security:
- `.claude/settings.json` auto-allows `Bash(python3 -c *)`. Never open this repo as a Claude Code project.
- The pptx builder ships an auto-updater (`git pull` + `pip install`).
- A watermark remover strips AI-provenance marks. Do not use it; it conflicts with synthetic-content disclosure.

Ideas re-implemented independently in our own code:
- A render-twice determinism check (`tests/test_render.py`).
- An integer-frame timeline (already in `timeline.py`).
- An asset manifest with hashes (`reports/asset-manifest.json`).
- A "1 recommended + 2 alternatives" style proposal (`art_direction.propose_styles`).

## 8. Render evidence for adapter integrations

See `references/style-registry.md` (generated from `styles/registry.json`). A style is listed as `operational` only after a sample render produced a valid MP4 on this machine, and the sample path is recorded in the registry.
