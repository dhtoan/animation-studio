# sweety_handdraw (vendored)

- Upstream: https://github.com/threerocks/sweety-handdraw-video
- Commit: `5206ec0d17f9b353e400b64b9c51ad69e721e02a`
- Licence: MIT, Copyright (c) 2026 threerocks (`LICENSE`, copied verbatim)
- Used by: `scripts/studio_lib/engines/sweety_draw.py` (engine `sweety_draw`)

## Files

| here | upstream (`skills/sweety-handdraw-video/scripts/`) | changes |
|---|---|---|
| `stroke_paths.py` | `stroke_paths.py` | docstring replaced by attribution header; body verbatim |
| `paint_motion.py` | `paint_motion.py` | attribution header added; body verbatim |
| `stroke_assets.py` | `stroke_assets.py` | see below |
| `reveal.py` | `video_renderer.py`, `drawing_contract.py`, `video_verifier.py` | see below |

### `stroke_assets.py`
Verbatim: `lengths`, `ordered_paths`, `time_paths`, `measure_text`, and the planning core of
`build_text` / `build_illustration` (outline strokes for every part in order, then brush painting
for every part in the same order; ink/colour two-channel reveal maps).

Changed:
- No global asset directory, no file writes. `build_text(text, size, color, font_path)` and
  `build_illustration(pil_image, max_w, max_h, parts)` return `(rgba, maps, metadata)`; the
  engine caches them.
- `build_brush` (marker highlights) and the source-path/crop handling were dropped.
- `build_illustration`:
  - it skips empty parts, where upstream raised;
  - parts with no outline pixels are painted only, where upstream raised;
  - visible pixels outside every polygon go to an implicit trailing `rest` part, where upstream raised;
  - fill pixels are reassigned per colour component to the part that owns most of that component, so a large fill crossing a polygon edge is painted in one piece (no straight seams mid-fill);
  - pixels that no pass reaches are revealed at the end.

### `reveal.py`
- `ease` and `point_on_asset` come from `video_renderer.py`. They are verbatim, except that `point_on_asset` takes `segments` instead of the metadata dict.
- `reveal_alpha` is the array form of `video_renderer.Renderer.layer`. The maths is unchanged.
- `pen_position` is adapted from `video_renderer.Renderer.pen`, with these changes:
  - between drawing groups the pen glides on an arc to the next stroke, where upstream sent it off-screen when the gap was over 0.25 s;
  - it eases in before the first group and out after the last;
  - the nib is clamped to the canvas.
- `validate_strokes` is verbatim from `drawing_contract.py`.
- `match_reveal_to_tip` is verbatim from `video_verifier.py`.

## Not vendored
Everything that is not drawing: the job/manifest compiler, art-direction and style gates,
narration master/alignment, captions/subtitles, audio mixing, watermark, the cover second,
the hosted hand sprites and the voice studio. The engine supplies timing, captions and audio.
