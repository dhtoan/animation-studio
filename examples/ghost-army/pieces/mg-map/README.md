# mg-map: g02 (Ghost Army)

This is a night military map of the Rhine sector near Viersen in March 1945, as German observers on the east bank would have seen it.

It is the setup for g03's reveal, so the two American infantry divisions (30th and 79th) appear real:
- solid friendly-infantry division symbols;
- columns of trucks, tanks and towed guns moving along roads into position;
- engine sound rings toward the east bank;
- radio traffic between the two division HQs, intercepted by the observers.

There are no "simulated" labels and no contested figures here.

It is drawn on a 2D canvas (no WebGL) and works in headless Chromium without a GPU.

## Later map eras (`eras.js`)

These share one piece clock with g02 (`params.era: true`; the default clock lays them end to end in film order). Each era starts clean with its own camera. g02's drawing code is unchanged.

| Era | Content |
|---|---|
| g20 | Normandy: the journey ahead, then Omaha Beach. The D-Day card (four landed; two became casualties building false beach landing sites) is shown as muted figures, with no injury imagery. A Seymour Nussenbaum card follows. |
| g23 | Route Normandy → Brittany → the siege of Brest (Aug 1944). Visual, sonic and radio deception combine, labelled "according to one nonprofit account" (a contested claim). |
| g24 | Recap, then Luxembourg: a schematic Third Army line with its thinly held stretch near Bettembourg, a simulated 6th Armored Division, and bars comparing about 500 men with about 8,000. |
| g26 | Bastogne besieged. The fake radio traffic and the Third Army moves it suggested are drawn as dashed arrows. |
| g28 | The reveal, on g02's sector geometry. Solid units and columns flip to dashed **SIMULATED** decoys, German attention is drawn to them, and the Ninth Army's real crossing to the north appears (approximate position). |
| g31 | Italy: the 3133rd Signal Service Company, Operation Craftsman (April 1945) and a schematic Gothic Line north of Florence. Panels show about 200 soldiers, 19 days in combat, and 35 dummy tanks with "almost 70%" lost to German fire, drawn as dimmed glyphs. |

Fronts, routes, arrows and the Gothic Line are schematic. Every era carries an "approximate positions" note.

## Narration beats (`timing.js`)

g02 narration: *"Not far from the front, they could see it: the trucks, the tanks and the artillery of two American infantry divisions moving into position. They could hear engines at night. They could pick up the radio traffic."*

Beats are keyed to words. They come from the injected `window.STUDIO_TIMING` word times. When those are absent, each word's character position is spread over the scene length.

| Word | Beat |
|---|---|
| *see* | observers and sight cones |
| *trucks* / *tanks* / *artillery* | the three columns start; they arrive by *position* |
| *two* / *infantry* | the division symbols land |
| *engines* | sound rings |
| *radio* | radio traffic and intercept |

The camera pushes in from the lower Rhine until *trucks*. The scene length comes from the timing, not from a constant.

## Rendering

Render through `html_seek` as a project page. It is mounted at `/@film/` under the lemo contract. `main.js` also exposes `window.renderFrame` and mg-styles-15's `window.renderAt` / `window.__ready` / `window.DEMO`, so it also works with the generic contract and with mg's `harness/render.mjs`.

```json
{"page": "pieces/mg-map/index.html", "era": true,
 "timing": {"fps": 30, "scenes": [{"id": "g02", "start": 0, "end": 14.4667}]}}
```

`window.MIN_TEXT(t)` reports the smallest readable label, which is at least 28 px. The graticule ticks, the scale-bar text and the "approximate positions" note are deliberately smaller.

## Accuracy

These are approximate and illustrative, and the map is labelled "approximate positions · schematic roads":
- the Rhine course (hand-entered coordinates, drawn as a Catmull-Rom curve);
- town positions;
- the approach roads (schematic, not real roads);
- the division and observer positions.

Country borders are modern (Natural Earth 1:110m) and are shown only on the wide opening shot.

## Credits and licences

| Files | Source | Licence |
|---|---|---|
| Approach: topojson, then `d3.geoPath` on a canvas; HUD map look | `demos/22-hud` of [mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) (the ga-map prototype built on it) | MIT, © 2026 Vincentwei1021. No mg code is copied verbatim; `film.js`, `timing.js`, `main.js` and `index.html` are ours. |
| `data/land-50m.json` | as shipped in mg-styles-15 `demos/22-hud/assets/`; TopoJSON in the world-atlas 2.x layout | Natural Earth data, public domain. world-atlas packaging (Mike Bostock) is ISC. |
| `data/countries-110m.json` | as shipped in mg-styles-15 `demos/19-paperclip/assets/`; world-atlas 2.x layout | Natural Earth, public domain. world-atlas is ISC. |
| `lib/d3-array.min.js` v3.2.4, `lib/d3-geo.min.js` v3.1.1 | Mike Bostock; d3-geo also includes Charles Karney's code | ISC (`lib/LICENSE.d3-array`, `lib/LICENSE.d3-geo`) |
| `lib/topojson-client.min.js` v3.1.0 | Mike Bostock | ISC (`lib/LICENSE.topojson-client`) |
| `fonts/Inter.ttf`, `fonts/LeagueGothic.ttf`, `fonts/IBMPlexMono-Medium.ttf` | Google Fonts | SIL OFL 1.1 (`fonts/OFL-*.txt`) |
