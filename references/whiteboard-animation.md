# Whiteboard animation

## `whiteboard` engine (native)
- **Look:** a marker on a board texture. Ink strokes have a subtle wobble, and flat translucent fills land after the outline (`fill_after` = 72 % of the draw). Hand-lettered text is revealed left to right.
- **Pen:** a procedural pen and hand (original artwork) follow the tip of the active stroke.
- **Draw order:** elements draw in the order they are listed, gated by their `at` cues. Within one element, outlines draw by cumulative length.
- **Elements that work well:**
  - `icon`, `arrow`, `process`, `timeline`
  - `list` with marker `check`, `cross` or `num`
  - `shape`: `circle`, or `x_mark` to annotate
  - `text` with `underline`

## `image_whiteboard` engine: draw a supplied illustration
Set `params.src` to a PNG or JPG in the project, and record its licence in `assets[]`. The engine then:
1. Fits the image into `box` and thresholds the ink (`ink_threshold`, default 110).
2. Plans the line pass with one of two vendored upstream planners:
   - `order: "strokes"` (default): a Zhang–Suen skeleton traced into pen strokes, so the pen follows real strokes. Source: `adapters/vendor/sweety_stroke_paths` (MIT, from threerocks/sweety-handdraw-video).
   - `order: "grid"`: 10 px ink cells, ordered by connected components with bridge splitting and a gradient walk. Source: `adapters/vendor/srt_whiteboard_grid` (MIT, via letuandat131/whiteboard-animation-vi).
3. Reveals colour in a top-to-bottom sweep, starting after `line_share` (default 0.62) of `draw_time`.

It works best with clean line art on white. Photos and dark images give noisy ink maps; use the `artistic` or `handdrawn` engine for those.

## Tips
- Keep each board to at most 6 drawn objects. Use `until` to clear a region before the next idea.
- Use `transition: "erase"` (an eraser swipe) between consecutive whiteboard scenes.
- Draw durations:
  - icons: 0.8–1.4 s
  - process boxes: about 1 s per step
  - text: about 0.6 s per line
