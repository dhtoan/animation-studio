# Source audit

Audit date: 2026-10-14. All repositories were shallow-cloned read-only into `_upstream/` (git-ignored, not part of the skill) and never modified.
"Verified" means read in code or executed here (Windows 11, Python 3.14, Node 24, 4 CPU, no GPU work).
"Inferred" means a reasonable reading that was not executed.

| Repo | Commit | License | Decision |
|---|---|---|---|
| alchaincyf/huashu-art-motion | `2571ee0` (2026-10-14) | MIT (fonts OFL; likeness/mascot assets excluded) | **External adapter** (`huashu_clip` engine drives its Canvas2D clip grammars through Playwright) |
| letuandat131/whiteboard-animation-vi | `c689bf7` (2026-10-13) | CC0 original code; `grid_stream.py` MIT (SRT Whiteboard); ISNet Apache-2.0; hand PNGs **unlicensed** | **Vendored** `grid_stream.py` (+ MIT notice) into `adapters/vendor/srt_whiteboard_grid/` |
| cth9191/motion-design | `b1a35f4` (2026-09-06) | **No license** (all rights reserved; prompts are third-party text) | **Reference only.** No text, prompts or images copied |
| cth9191/animate | `7e5eb56` (2026-10-05) | MIT | **External adapter** (`animate_piece` engine builds a piece with its `build.mjs` and captures `renderFrame(t)`) |
| threerocks/sweety-handdraw-video | `5206ec0` (2026-10-13) | MIT (hosted AI hand sprites: uncertain rights; `waner-brush` has character-IP risk) | **Vendored** `stroke_paths.py` (+ MIT notice) into `adapters/vendor/sweety_stroke_paths/` |

---

## 1. huashu-art-motion (MIT © 2026 alchaincyf)

**What it is (verified).** A deterministic, frame-by-frame **Canvas2D engine**. Playwright opens `scripts/engine/clip.html` (or `index.html` for "films"), injects `window.CLIP_SPEC`, calls `prepare(t)` and `renderFrame(t)`, reads `canvas.toDataURL('image/png')` and pipes the PNG into ffmpeg (`scripts/engine/render.py`).

**What it contains:**
- 35 art-history style scenes.
- 8 parameterised explainer grammars in `clips/*.js`: `t1_3b1b`, `t2_keynote_ui`, `t3_finance_chart`, `y1_kurzgesagt`, `y2_vox`, `y3_whiteboard`, `y4_storytime`, `y5_kinetic_type`. Each has an example JSON spec.
- JS libraries in `lib/`: motion, camera, typo, chart, diagram, media, palettes, and others.
- `transitions.js` with about 30 transitions.
- QA gates: `film_gate.py`, `qa.py`, `storyboard_lint.py`.
- A procedural music synth template.

**Clip spec contract (verified):**
```
{grammar, duration, fps, width, height, safe{...}, theme, data,
 cues: [{at, kind, text, sub, image, data}]}
```
Frame `i` is rendered at `t = i/fps`.

**Formats:** default 1920×1080. 9:16 is possible via width/height, but the art scenes are landscape-only. Output is H.264 CRF 14, or ProRes 4444 with alpha.

**Claims vs reality:**
- "Narrated film" support is reference code. The timing builder and the author's pipeline wrapper are not in the repo, and there is no ASR or alignment.
- Voice is macOS `say` or the Volcengine cloud API only. Windows/Linux system voice is documented as not implemented.
- Characters come from external image generation.
- The author's live Claude Code regression was not completed (blocked by a 429).

**Tests (verified):** `python -B -m unittest discover -s tests` gave 97 tests: 4 errors, 6 skipped, the rest passed.
- The errors are environmental: missing `ffprobe` and missing `requests`.
- On Windows the scripts crash under cp1252 unless run with `-X utf8`.

**Here (verified):**
- The Python `playwright` 1.64 package was installed as a dev dependency.
- Its bundled browser revision is not downloaded, but the existing `ms-playwright/chromium-1234` launches with `executable_path`.
- Our adapter renders the upstream clip grammars from an external checkout (see `references/rendering.md`).

**Limitations:**
- Rendering is serial, one PNG round-trip per frame, so it is slow.
- Docs and CLI are in Chinese.
- QA gate thresholds were calibrated by one author.

**Do not reuse:**
- Huashu likeness/character frames.
- Clawd mascot assets.
- `spacex_wb/assets/strokes.js` (Arphic license).
- The `git ls-remote` self-update check.

## 2. whiteboard-animation-vi (CC0 + MIT + Apache-2.0)

**Engine (verified).** `handdraw/render.py:render_video(image, settings)` reveals an *existing raster image*. The steps:
1. Ink map: bilateral filter, CLAHE, adaptive threshold.
2. Ink cells on a 10 px grid, ordered by `grid_stream.py` (connected components, bridge splitting, text / contour / subject classes, gradient walk, nearest-exit chaining).
3. Colour fill: Lab k-means palette, angled brush lanes, travel-optimised routing.
4. A torch `grid_sample` deforms photographic hand sprites.
5. Encode with libx264 or NVENC.

The README claims match the code. It is a raster cell reveal, not a vector tracer.

**Dependencies (verified by per-module import):**
- Every render path needs cv2 and torch; scipy and skimage are needed for fills; Gradio for the UI.
- Defaults are `device='cuda'`, `encoder='nvenc'`, plus a 204 MB ISNet checkpoint.
- There is no CLI; the entry points are the Gradio app or the Python API.
- **Only `grid_stream.py` is portable:** it needs just `cv2.connectedComponents`.

**Tests:** `tests/*` (16 cases) were not runnable here because pytest, cv2, torch and gradio are absent. The audit ran `grid_stream` unchanged behind a numpy labelling shim: a 320×180 drawing gave 139 cells, 1 stream, every cell ordered exactly once, and a valid MP4.

**Licensing:**
- `grid_stream.py` is MIT (© 2026 江哥是老登啊; notice at `vendor_runtime/srt_whiteboard/LICENSE`).
- The rest of the original code is CC0.
- **Hand PNGs: "No redistribution license has been selected", so they are not reused.**

**What we took:** `grid_stream.py`. The only change is an optional `cv2` import with a pure-numpy 8-connectivity fallback. It is used by the `image_whiteboard` engine (`order: grid`).

## 3. motion-design (cth9191): no license

**What it is (verified).** A prompt library and workflow skill for the **Higgsfield MCP**: Seedance video plus GPT Image references. That service is paid and requires an account. It holds 10 presets (archived source prompts, adaptation templates, recipes) and a gallery builder (`build_gallery.py` validates 10 presets: verified).

**Claims vs reality:** It renders nothing locally, and its SKILL.md forbids local substitutes. The README images are frames from Higgsfield's own source videos, not output from the skill. Per ROADMAP, there is no evidence that the presets reproduce the sources.

**License:** there is no LICENSE file. ATTRIBUTION.md says "No repository-wide license has been applied", and the prompts are third-party. **Nothing is copied.** Our `references/motion-graphics.md` is independently written; it links to the repo as optional further reading and as a "generative video" route that needs a paid service and explicit user approval.

## 4. animate (MIT © 2026 cth9191)

**Engine (verified):**
- **Build:** `tools/build.mjs <piece>` concatenates `head.html`, `kit/core.js`, `styles/<s>/kit.js`, `src/scenes.js`, `src/bridges.js`, `kit/morph.js`, `kit/board.js`, `kit/score-head.js`, `src/score.js` and `kit/score-tail.js` into one self-contained `index.html` with one canvas.
- **Export:** `tools/export.mjs` uses npm `playwright` to step `window.renderFrame(i/fps)`. Audio is rendered in an `OfflineAudioContext` (`window.renderAudioWav`).
- **Styles:** 7 (crosshatch, cut-paper, isometric, math, pixel, riso, sketchbook).
- **Motion:** shape-morph "bridges" between eras, 24 fps with 12 fps line boil, and `?format=` relayout for 9:16, 1:1, 4:5 and 16:9.

**Here (verified):**
- `build.mjs` succeeds for `examples/history-of-ai`, all 7 style demos and both templates.
- Headless Chromium screenshots render correctly.
- `export.mjs` was not run as-is, because the npm `playwright` package and ffmpeg on PATH are missing. Our adapter replaces only the capture step: Python Playwright plus the existing Chromium.

**Limitations:**
- Pieces are code-heavy (the example `scenes.js` is 48 KB).
- 2D canvas only.
- Voice uses ElevenLabs and faster-whisper (both external).
- Only some formats are proven, per its own "Honesty" section.

## 5. sweety-handdraw-video (MIT © 2026 threerocks)

**What it is (verified).** A gated compositor. The agent writes the script, design, drawing plan and part polygons, and generates every image with the host's image tool; no script calls an image API. Python then does:
- ink/outline extraction;
- Zhang–Suen thinning and graph stroke tracing (`stroke_paths.py`, numpy only);
- outline-first then fill ordering;
- PCA-oriented brush fills (`paint_motion.py`, needs scipy);
- a hand-sprite renderer;
- burned-in captions;
- ffmpeg (loudnorm I=-20).

TTS is VoiceStudio (Qwen3-TTS) or VoxCPM2, both **MLX only (Apple Silicon)**. There is no automatic alignment.

**Tests (verified):** raw, 17 run with 15 errors (scipy, requests, cp1252). With `-X utf8`, a numpy `scipy.ndimage` shim, ffmpeg on PATH and a Windows font: 52 run, 0 failures, 2 errors (requests; a Windows file-handle cleanup). A demo render produced a valid 10.8 s MP4. The docs state only macOS + Codex was tested end to end.

**Hand sprites:**
- Not in the repo; they are GitHub-release downloads.
- They are AI-generated, and the copyright status is uncertain.
- `waner-brush` is "inspired by" a game character.
- **Not reused.** Our pen and hand are drawn procedurally.

**What we took:** `stroke_paths.py`, unmodified apart from a provenance header. It is used by the `image_whiteboard` engine (`order: strokes`) to trace real pen strokes from an illustration.

## 6. X post: @leo_xiaolei, status 2109982650199060818

**Accessed:** 2026-10-14 through the in-app browser, with the text readable without login. Posted 2026-10-13, 7:20 PM, with about 73.6K views when read. The images, the 49-second demo video and the voice samples were **not** inspected frame by frame. Only the post text was read.

**Verified content (paraphrased from the Chinese text):**
- It announces the open-sourcing of **sweety-handdraw-video** (github.com/threerocks/sweety-handdraw-video). The post promotes it as the strongest hand-drawn video pipeline available, and says it runs perfectly under ChatGPT/Codex.
- Pipeline claims: an "AI director" storyboards from a script or topic, and the user can steer it ("open on the conflict", "don't add a moral").
- Drawing claims: the engine "reads" each generated illustration, splits it into parts (head, body, background, props) and draws outline then fill in a human-like order.
- Assets: 6 hand and brush combinations, with a watermark possible on the brush.
- Voice: VoxCPM 2, described as heavy on weaker machines.
- Requirements: an agent with image generation, Python 3.9+ with Pillow, NumPy and SciPy, FFmpeg/ffprobe, and a local TTS.
- Cost: no paid video-generation API. Assets are decoupled and re-rendered locally. The author reports using under 1% of a $200 subscription.
- Default output: 1920×1080 at 30 fps, MP4 plus cover, subtitles, script and a check log.
- Install: `npx skills add threerocks/sweety-handdraw-video --skill sweety-handdraw-video`.
- It mentions a possible future paid closed-source version.

**Checked against the code (section 5):**
- The part-wise outline-then-fill drawing claim matches the code. The "reading" of the image is done by the agent writing part polygons, not by a vision model inside the scripts.
- The tested platforms (macOS + Codex) and the MLX-only TTS mean the post's Windows and Claude usability is unverified.
- Superlatives such as "strongest" are marketing, not measurable claims.

---

## Source → feature integration matrix

| Studio feature | Our implementation | Upstream reuse | Status |
|---|---|---|---|
| Whiteboard (vector, from scene spec) | `engines/whiteboard.py` | Pattern: progressive stroke and pen tip (sweety, wb-vi) | Operational |
| Whiteboard from an illustration | `engines/image_whiteboard.py` | **Code:** wb-vi `grid_stream.py`, sweety `stroke_paths.py` | Operational |
| Hand-drawn / sketch | `engines/handdrawn.py` | Pattern: line boil on 2s and hatching (animate) | Operational |
| Motion graphics / charts | `engines/motion.py` | Pattern: cue-at-time contract (huashu) | Operational |
| Kinetic typography | `engines/kinetic.py` (word-synced to TTS timings) | Pattern: huashu y5 | Operational |
| Artistic / atmospheric | `engines/artistic.py` | Pattern: parallax, grain, vignette | Operational |
| huashu grammars (3b1b, Vox, finance chart…) | `engines/huashu_clip.py` | **External engine** via Playwright | Operational when a huashu checkout and Chromium are configured |
| animate pieces (cut-paper, riso, …) | `engines/animate_piece.py` | **External engine** (`build.mjs` + capture) | Operational when an animate checkout, Node and Chromium are configured |
| Generative video (Higgsfield) | not implemented | motion-design is reference only | Out of scope (paid service) |
| TTS | `tts.py`: sapi (local Windows), edge (opt-in network), file, estimate | none (upstream TTS is macOS/MLX/cloud) | sapi operational on Windows |
| Music / SFX | `audio.py` procedural synth | Pattern: procedural score (huashu, animate) | Operational |
| QA gates | `qa.py` | Pattern: film_gate motion and blank checks (huashu) | Operational |
