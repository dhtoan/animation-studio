# lemo-blueprint — g06 (Ghost Army)

An orders / routing sheet drafted live on cyanotype paper with the **blueprint engine of
[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)** (MIT licence), **imported from the library at
run time, not copied**: `/styles/blueprint/demo/draw.js` (line, solid, hatch, text, balloon, nibs),
`/styles/blueprint/demo/paper.js` (WebGL2 sheet compositor), `/styles/blueprint/demo/sheet.js`
(border, hand shadow) and `/core/lib.js`. Fonts: Architects Daughter and B612 (SIL OFL 1.1), requested
at `/styles/blueprint/demo/fonts/` and served from `tools/fonts/` (`python scripts/fetch_fonts.py`).
Our files here: `index.html`, `main.js`, `film.js`, `timing.js`.

| era | content | default |
|---|---|---|
| g06 | order block: activated 20 JAN. 1944, Camp Forrest, Tenn., 23rd HQ Special Troops, Col. Harry L. Reeder, for the rest of the war; then FIG. 1 route schematic: Camp Forrest → training → ship out → Atlantic crossing → England → France, labelled NOT TO SCALE | 0–20 s |

Nothing beyond the g06 narration is stated: no dates, ports or numbers are added, and the route is a
schematic, not a map. Fields and stations are lettered on the narration words (`timing.js`), with
minimum holds. The camera never leaves the sheet; all text is at least 28 px font size at 1080p
(`window.MIN_TEXT(t)`), except the engine's own border zone markers.

## Rendering

`{"page": "pieces/lemo-blueprint/index.html", "era": "g06", "timing": {"fps": 30, "scenes": [{"id": "g06", "start": 0, "end": 20}]}}`
through `html_seek`, or `node core/render/video.mjs <this folder> --fps 30` from the lemo library root.
