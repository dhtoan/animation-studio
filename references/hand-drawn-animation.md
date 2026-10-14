# Hand-drawn animation (`handdrawn` engine)

## Look
- Cream paper with grain and a vignette.
- Pencil lines with a low-frequency wobble that **boil on 2s**: three variants cycle at 8 fps, the classic way hand animation keeps a line looking alive.
- An optional second ghost line (`double_line`).
- Two fill styles:
  - `wash` (default): soft watercolour.
  - `hatch` (`params.fill: "hatch"`): diagonal pencil hatching clipped to the shape.

## Characters (`type: "character"`)
- An original simple figure with idle sway and blinks.
- Optional `talk` mouth flaps.
- Poses: stand, point, shock, think, celebrate, slump.
- Pose changes over time: `poses: [{at: "cue:word", pose: "slump"}]`.

## When to use it
Personal stories, founders, decisions, "inside the room" moments and historical recreations. Label recreations as illustrative.

## Upstream context
The boil-on-2s and hatching ideas follow common practice that cth9191/animate's sketchbook and crosshatch styles also use (MIT). No code was copied from it. To render a full animate piece, use the `animate_piece` engine.
