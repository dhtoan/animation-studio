# Ghost Army: crosshatch scenes

A timing-driven animated piece for ten Ghost Army scenes (`g01 g03 g04 g05 g10 g11 g13 g14 g18 g19`). It is drawn in code in the
crosshatch ink style: line boil on 2s, hatch and pencil shading, and red that means *fake* and nothing else.

## Attribution

The renderer (`kit/morph.js`), the drawing kit (`kit/core.js`), the crosshatch style (`styles/crosshatch/kit.js`), the score synth
(`kit/score-*.js`) and the tools (`tools/build.mjs`, `tools/export.mjs`) are **(c) cth9191/animate, MIT licence**. They are used from the
external checkout `_upstream/animate/plugins/animate/skills/animate` and are not copied here. This folder holds only this piece's
own `src/` parts: the head, the timeline, the helpers prefixed `ga*`, the eras, the bridges and the score.

## Timing

`src/timing.js` defines `window.GA_TIMING = { fps, scenes: [{ id, start, end, bridge_next }] }`. Everything is derived from it:
- the eras and `DURATION`;
- each era's beats, placed at fractions of its length with minimum and maximum holds (`gaAt` in `src/timeline.js`);
- the captions;
- the shape-morph bridges, built only where `bridge_next` is true, with 0.24 s on blank paper;
- the score.

Boundaries snap to the frame grid, so a clean cut lands exactly on the next scene's first frame.

The studio pipeline never edits this folder. `AnimatePieceEngine` (`params.timing`) writes its own `src/timing.js` into a work
copy, keyed by a build hash, and renders scene X with `offset = start_X` for `end_X - start_X` seconds.

## Build and export (native)

Copy the folder elsewhere first, so build output stays out of the repo:

```
cp -r examples/ghost-army/pieces/crosshatch /tmp/ga
node <animate>/tools/build.mjs /tmp/ga
node <animate>/tools/export.mjs /tmp/ga        # frames/, renders/audio.wav, renders/final.mp4
```

Both need Node, Playwright Chromium and ffmpeg on PATH.

## Facts

On-screen facts come only from the project dossier. g14 is labelled as an oral history and illustrative recreation. The g11
portraits and the g05 officer are illustrative (no likeness). The markings stencilled in g18 are deliberately unreadable.
