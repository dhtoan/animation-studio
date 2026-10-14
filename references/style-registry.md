# Style registry

Generated from `styles/registry.json` + `styles/verification.json` (`studio.py styles --verify`).
**operational** = sample rendered and validated on the verifying machine; **declared** = not yet verified here; **failed** = verification attempted and failed (see error).

| Style ID | Engine | Source / licence | Aspects | Status | ms/frame | Best for | Dependencies |
|---|---|---|---|---|---|---|---|
| `native.whiteboard` | whiteboard | native · project | 16:9, 9:16 | **operational** | 121.4 | explain, process, tutorial, timeline | — |
| `native.handdrawn-wash` | handdrawn | native · project | 16:9, 9:16 | **operational** | 69.6 | story, character, recreation | — |
| `native.handdrawn-hatch` | handdrawn | native · project | 16:9, 9:16 | **operational** | 86.0 | story, history | — |
| `native.motion-dark` | motion | native · project | 16:9, 9:16 | **operational** | 69.3 | data, comparison, evidence, reveal | — |
| `native.kinetic` | kinetic | native · project | 16:9, 9:16 | **operational** | 54.8 | hook, quote, cta | — |
| `native.artistic-night` | artistic | native · project | 16:9, 9:16 | **operational** | 99.2 | atmosphere, metaphor, reveal | — |
| `native.image-whiteboard` | image_whiteboard | native+vendored (sweety stroke_paths MIT, SRT grid MIT) · MIT notices in adapters/vendor | 16:9, 9:16 | **operational** | 99.0 | illustration | an illustration asset with a licence |
| `huashu.finance-chart` | huashu_clip | alchaincyf/huashu-art-motion · MIT | 16:9, 9:16 | **operational** | 691.5 | data | huashu checkout, playwright, chromium |
| `huashu.kinetic-type` | huashu_clip | alchaincyf/huashu-art-motion · MIT | 16:9, 9:16 | **operational** | 899.2 | hook, quote | huashu checkout, playwright, chromium |
| `huashu.3b1b` | huashu_clip | alchaincyf/huashu-art-motion · MIT | 16:9 | **operational** | 863.6 | explain, science | huashu checkout, playwright, chromium |
| `animate.cut-paper` | animate_piece | cth9191/animate · MIT | 9:16, 16:9, 1:1 | **operational** | 1059.2 | timeline, history | animate checkout, node, playwright, chromium |
| `lemo.whiteboard` | html_seek | lemomo-ai/lemo-opuscar · MIT (demo assets per CREDITS) | 16:9 | **operational** | 310.1 | explain | lemo checkout, playwright, chromium, upstream font binaries are not in git; html_seek serves a local fallback font (degraded typography) unless you supply the OFL fonts |
| `lemo.pixel-rpg` | html_seek | lemomo-ai/lemo-opuscar · MIT (demo assets per CREDITS) | 16:9 | **operational** | 550.8 | story, history | lemo checkout, playwright, chromium |
| `dashi.handdrawn-notes` | html_seek | chuspeeism/dashi-animationstyle · MIT | 16:9 | **operational** | 135.4 | explain | dashi checkout, playwright, chromium |
| `dashi.black-gold-tech` | html_seek | chuspeeism/dashi-animationstyle · MIT | 16:9 | **operational** | 225.1 | hook, technology | dashi checkout, playwright, chromium |
| `dashi.flat-flowchart` | html_seek | chuspeeism/dashi-animationstyle · MIT | 16:9 | **operational** | 101.6 | process | dashi checkout, playwright, chromium |
| `mg.flat-vector` | html_seek | Vincentwei1021/mg-styles-15 (tree 49052d8, source files only) · MIT (fonts not distributed upstream) | 16:9 | **operational** | 908.1 | explain, hook | mg-styles-15 source checkout, playwright, chromium, font fallback (upstream fonts not distributed) |
| `mg.pixel` | html_seek | Vincentwei1021/mg-styles-15 (tree 49052d8, source files only) · MIT (fonts not distributed upstream) | 16:9 | **operational** | 134.1 | story, history | mg-styles-15 source checkout, playwright, chromium, font fallback (upstream fonts not distributed) |
| `mg.liquid` | html_seek | Vincentwei1021/mg-styles-15 (tree 49052d8, source files only) · MIT (fonts not distributed upstream) | 16:9 | **failed** | 1070.4 | title, metaphor | mg-styles-15 source checkout, playwright, chromium, font fallback (upstream fonts not distributed) |

Descriptions:

- `native.whiteboard`: Marker strokes on a board with pen cursor; translucent fills after outlines; hand lettering.
- `native.handdrawn-wash`: Cream paper, boiling pencil lines on 2s, soft watercolour wash fills.
- `native.handdrawn-hatch`: Pencil drawing with diagonal hatching fills.
- `native.motion-dark`: Flat vector motion graphics on a navy field with drifting grid; charts, counters, networks.
- `native.kinetic`: Narration-synced kinetic typography with accent emphasis words.
- `native.artistic-night`: Gradient sky, parallax silhouettes, lit windows, fog, grain, vignette.
- `native.image-whiteboard`: Redraws a supplied line illustration stroke by stroke, then colours it.
- `huashu.finance-chart`: Paper-toned editorial bar/line chart grammar with source line and highlight.
- `huashu.kinetic-type`: Poster-style kinetic typography grammar (numbers, points, highlight).
- `huashu.3b1b`: Dark math/diagram grammar from huashu's clip library.
- `animate.cut-paper`: Cut-paper style piece with shape-morph bridges (example: history-of-ai).
- `lemo.whiteboard`: lemo-opuscar whiteboard film engine with stroke physics and camera. Upstream demo film: "Einstein in Your Pocket" (111.0 s).
- `lemo.pixel-rpg`: 16-bit pixel-art RPG film engine. Upstream demo film: "The Last Save Point" (54.5 s). The only lemo demo whose assets are fully present in git at fdc46d7.
- `dashi.handdrawn-notes`: Off-white paper, ink-blue line art with orange, stroke-by-stroke writing with following pen.
- `dashi.black-gold-tech`: Near-black with gold hairlines; serif text resolving from blur.
- `dashi.flat-flowchart`: Cream background, amber title band, numbered horizontal flow.
- `mg.flat-vector`: Bright flat SVG character scene with spring pops. 10 s upstream demo film.
- `mg.pixel`: 320x180 pixel side-scroller with a CRT pass. 10 s upstream demo film.
- `mg.liquid`: Glossy WebGL2 SDF metaballs forming a wordmark. 10 s upstream demo film.
