# Motion graphics and kinetic typography

## `motion` engine
A dark gradient field with a slowly scrolling grid. Elements pop in (`ease_out_back`), slide in (`anim: "slide"`) or fade in.

Elements:
- `bar_chart`: bars grow with a stagger and values count up. Supports `prefix`, `suffix` and `decimals`.
- `line_chart`: draws left to right with a moving head. `drop_index` turns later segments red; `mark` labels a point.
- `donut`: sweeps in, with a centre label.
- `counter`: counts with an ease-out, with an optional label.
- `network`: nodes appear, then edges. `break_at` + `broken` snaps links red with an ✕.
- Also: `timeline`, `process`, `list`, `card`, `stamp`.

## `kinetic` engine
Builds phrases word by word, timed to the measured TTS word times.
- `params.emphasis`: words drawn in the accent colour.
- `max_words`: phrase length (5 for 16:9, 3 for 9:16).
- `size`: type size.
- When the next phrase begins, the previous one drifts up and fades.

## `huashu_clip` adapter
Renders the clip grammars of alchaincyf/huashu-art-motion from an external checkout: `t1_3b1b`, `t2_keynote_ui`, `t3_finance_chart`, `y1_kurzgesagt`, `y2_vox`, `y3_whiteboard`, `y4_storytime`, `y5_kinetic_type`.
- Params: `{grammar, theme, data, cues[{at, kind, …}]}`.
- `at` in cues accepts our `cue:word` syntax.
- Upstream examples: `scripts/engine/examples/*.json`.

## Motion density (house rules)
- Make a visible change every 2–3 s, and a larger change every 5–8 s.
- Use no more than three full-frame impacts (stamps, slams) per video.
- Numbers on screen must match both the narration and the ledger.
- Charts state their units, plus either "(fictional)" or the source, on screen.
- Text must be readable at phone size: nothing below `label` size, and high contrast.
