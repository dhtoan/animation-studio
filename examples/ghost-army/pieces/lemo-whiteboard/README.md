# lemo-whiteboard — g08 and g12 (Ghost Army)

Whiteboard-explainer segments drawn live (real progressive strokes, floating markers, board sheen,
camera motion blur) with the **whiteboard engine of [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)**
(MIT licence). The engine is **imported from the library at run time, not copied**:
`/styles/whiteboard/demo/engine/wb.js`, `/core/lib.js` and the single-line EMS Tech lettering
`/styles/whiteboard/demo/fonts/EMSTech.json` (SIL OFL 1.1, from the npm package `hersheytext`, MIT).
Our files here: `index.html`, `main.js` (lemo page contract), `film.js` (the two eras), `timing.js`.

| era | narration (production) | default |
|---|---|---|
| g08 | the 23rd built from four parts, in narration order: 603rd Camouflage (visual), Signal Co. Special (radio), 3132nd sonic company (sound), 406th Engineers (perimeter + staging) | 0–15 s |
| g12 | recap (about 1,100 men, many artists), "how?", four tools: things you see / hear, radio traffic, theater; small force made to look and sound large | 15–37 s |

Each era is its own board, timeline and camera, so a scene always starts clean. Beats are tied to
narration words (`timing.js`: injected word timings when the adapter has them, else the word's
position in the narration text spread over the era), so drawing scales with the era's length; every
drawing window has a minimum and maximum hold. Labels are at least 28 px cap height at 1080p in every
frame (`window.MIN_TEXT(t)` reports the smallest on-screen label).

## Rendering

Through our adapter (`engine: html_seek`), one studio scene per era:

```json
{"page": "pieces/lemo-whiteboard/index.html", "era": "g12",
 "timing": {"fps": 30, "scenes": [{"id": "g08", "start": 0, "end": 15}, {"id": "g12", "start": 15, "end": 37}]}}
```

`timing` is injected as `window.STUDIO_TIMING` before the page runs (it is part of the scene cache
key); `era` sets `offset` to that scene's start and injects its word timings. The lemo checkout must
be present (`_upstream/lemo-opuscar` or `STUDIO_LEMO_DIR`). Natively: `node core/render/video.mjs
<this folder> --fps 30` from the lemo library root.

Facts: only the project's Ghost Army dossier and narration. The tank is a generic Sherman-like
silhouette, not a technical drawing of a specific vehicle.
