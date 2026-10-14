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

## External projects driven by adapters (not shipped; use your own checkout)

| Project | License | Adapter |
|---|---|---|
| alchaincyf/huashu-art-motion | MIT © 2026 alchaincyf. Fonts are OFL. Likeness and mascot assets are excluded from MIT. | `engines/browser.py: HuashuClipEngine` |
| cth9191/animate | MIT © 2026 cth9191 | `engines/browser.py: AnimatePieceEngine` |

## Not used (licence or rights reasons)
- cth9191/motion-design: no licence; prompts are third-party.
- Upstream hand sprites and demo media: the whiteboard-animation-vi hand PNGs are unlicensed, and the sweety-handdraw-video hosted sprites are AI-generated with uncertain rights.

## Runtime dependencies (installed separately)
- Pillow (MIT-CMU)
- numpy (BSD-3)
- imageio-ffmpeg (BSD-2; bundles an FFmpeg build whose licence depends on the build)
- playwright (Apache-2.0)
- edge-tts (LGPL-3.0, optional)
