# Third-party notices

## Vendored code (shipped in this skill)

### adapters/vendor/srt_whiteboard_grid/grid_stream.py
- **Origin:** `handdraw/grid_stream.py` from letuandat131/whiteboard-animation-vi @ c689bf7, which derives from SRT Whiteboard.
- **License:** MIT, Copyright (c) 2026 江哥是老登啊. The full text is in `adapters/vendor/srt_whiteboard_grid/LICENSE`.
- **Modification:** `cv2` is now an optional import, with a pure-numpy 8-connectivity labelling fallback. The algorithm itself is unchanged.

### adapters/vendor/sweety_stroke_paths/stroke_paths.py
- **Origin:** `skills/sweety-handdraw-video/scripts/stroke_paths.py` from threerocks/sweety-handdraw-video @ 5206ec0.
- **License:** MIT, Copyright (c) 2026 threerocks. The full text is in `adapters/vendor/sweety_stroke_paths/LICENSE`.
- **Modification:** none, apart from a provenance header.

### adapters/vendor/sweety_handdraw/ (engine `sweety_draw`)
- **Origin:** `skills/sweety-handdraw-video/scripts/{stroke_paths, paint_motion, stroke_assets, video_renderer, drawing_contract, video_verifier}.py` from threerocks/sweety-handdraw-video @ 5206ec0.
- **License:** MIT, Copyright (c) 2026 threerocks. The full text is in `adapters/vendor/sweety_handdraw/LICENSE`.
- **Modification:**
  - The job, narration, caption, audio and cover machinery has been removed.
  - The builders return arrays instead of writing files.
  - Pixels that fall outside every part go to a trailing "rest" part.
  - The pen glides between groups and is clamped to the frame.
  - Every change is listed in `adapters/vendor/sweety_handdraw/SOURCE.md`.
- **Not shipped:** the hosted hand sprites. The pen is drawn by code.

## External projects driven by adapters (not shipped; use your own checkout)

| Project | License | Adapter |
|---|---|---|
| alchaincyf/huashu-art-motion | MIT © 2026 alchaincyf. Fonts are OFL. Likeness and mascot assets are excluded from MIT. | `engines/browser.py: HuashuClipEngine` |
| cth9191/animate | MIT © 2026 cth9191 | `engines/browser.py: AnimatePieceEngine` |

## External projects driven by `html_seek` (V2; not shipped)
| Project | License | Notes |
|---|---|---|
| lemomo-ai/lemo-opuscar | MIT © LemoLab | Demo assets per each demo's `CREDITS`. Font binaries are not tracked upstream; a local fallback font is substituted and logged. |
| chuspeeism/dashi-animationstyle | MIT © 2026 Dashi AI Lab | `动效部件.js` is copied into a work dir next to the page, as upstream `render.mjs` does. The example voice WAV is excluded. |
| Vincentwei1021/mg-styles-15 | MIT © 2026 Vincentwei1021 | Source files only were fetched. Fonts and media are not distributed. |

## Ideas and parameters ported with attribution (V2; no files copied)
- **Spring tiers and self-critique rubric:** Kianzzz/xilo-opus-video, MIT.
- **Camera and transition parameters** (crash zoom, iris, blinds, flash cut, glitch, light leak) and **shot-grammar rules:** Vincentwei1021/video-shotcraft, Apache-2.0.
  - NOTICE: "video-shotcraft, Copyright Vincentwei1021, licensed under the Apache License, Version 2.0."
  - Changes: re-implemented in Python/Pillow from the recipe parameter tables (`engines/base.py`, `references/shot-planning.md`).
- **Richness metric and motion-density rules:** chuspeeism/dashi-animationstyle, MIT.
- **Directing process** (treatment → shot list → cue map): lemomo-ai/lemo-opuscar `DIRECTOR.md`, MIT. Paraphrased.
- **Image art-direction rules:** threerocks/sweety-image-art-direction, MIT. Paraphrased in `references/image-art-direction.md`.

## V3 ports and data
- **Analytics query catalogue, date-lag window, batching and quota accounting:** nikhilbhansali/youtube-data-skills, MIT © 2025 Nikhil Bhansali. Re-implemented with fixes in `studio_lib/youtube_api.py`.
- **Median-baseline outlier method and comment-demand counting:** ravsau/youtuber-skills, MIT © 2026 CloudYeti. Paraphrased.
- **Natural Earth admin-0 countries (1:110m), v5.1.2:** public domain. Shipped in `examples/ghost-army/assets/`.
- **Research evidence in `examples/niche-research/`:**
  - Facts and figures observed on public web pages on 2026-10-14, with URLs.
  - Public YouTube page data was read by an automated script, not the API. Review YouTube's Terms of Service before automating this yourself; the Data API is the supported route.

## Not used (licence or rights reasons)
- cth9191/motion-design: no licence; prompts are third-party.
- Samin12/youtube-research-skill, joyjiangyi/youtube-research-pipeline: no LICENSE file.
- WaterDJiang/Wattter_openSkills: CC BY-NC-SA 4.0 (non-commercial). Its `.claude/settings.json` auto-allows arbitrary Python, so never open it as a project.
- Upstream hand sprites and demo media: the whiteboard-animation-vi hand PNGs are unlicensed, and the sweety-handdraw-video hosted sprites are AI-generated with uncertain rights.

## Runtime dependencies (installed separately)
- Pillow (MIT-CMU)
- numpy (BSD-3)
- imageio-ffmpeg (BSD-2; bundles an FFmpeg build whose licence depends on the build)
- playwright (Apache-2.0)
- edge-tts (LGPL-3.0, optional): uses Microsoft's online speech service. Check Microsoft's terms for your use.
