# lemo-whiteboard — g08, g12, g30, g36, g42, g43 (Ghost Army)

Whiteboard-explainer segments drawn live (real progressive strokes, floating markers, board sheen,
camera motion blur) with the **whiteboard engine of [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar)**
(MIT licence). The engine is **imported from the library at run time, not copied**:
`/styles/whiteboard/demo/engine/wb.js`, `/core/lib.js` and the single-line EMS Tech lettering
`/styles/whiteboard/demo/fonts/EMSTech.json` (SIL OFL 1.1, from the npm package `hersheytext`, MIT).
Our files here: `index.html`, `main.js` (lemo page contract), `film.js` (the eras), `timing.js`.

| era | narration (production) | default |
|---|---|---|
| g08 | the 23rd built from four parts, in narration order: 603rd Camouflage (visual), Signal Co. Special (radio), 3132nd sonic company (sound), 406th Engineers (perimeter + staging) | 0–15 s |
| g12 | recap (about 1,100 men, many artists), "how?", four tools: things you see / hear, radio traffic, theater; small force made to look and sound large | 15–37 s |
| g30 | a sketched page of Public Law 117-85 "findings": the quoted opening words of the postwar Army assessment highlighted (exact wording only, C34), its continuation labelled "paraphrase" | 9.37 s |
| g36 | one more chapter: the 23rd helped run displaced-persons camps; 13 tents and people as calm symbols; "the unit's history cites: up to about 100,000 people in 13 camps" | 14.03 s |
| g42 | our own sketch of the medal's four tools in four quadrants (telegraph operator, fake unit patch, loudspeaker half-track, inflatable tank), labelled "sketch, not the actual medal design"; the Army Secretary's remark at the ceremony as reported speech | 19.57 s |
| g43 | where the story lives on: Smithsonian Institution (the gold medal, by law), National WWII Museum exhibition (2020), Rick Beyer's documentary (2013, PBS); in Luxembourg the Bettembourg marker and the Limpertsberg monument (Sept. 7, 2023) | 32.17 s |

g30–g43 default to their narration-timed durations, placed one after another after g12 in
`timing.js`; in production each is rendered as its own scene with `era: true` and its word timings.
Cameras are shots that move and then hold; on held shots no label is cut by the frame
(`window.CLIPPED(t)` reports cut labels and whether the camera is holding).

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
