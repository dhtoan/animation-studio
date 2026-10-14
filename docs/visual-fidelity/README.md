# Visual-fidelity upgrade: comparison report

- Branch: `feature/visual-fidelity`
- Scope: the rejected Ghost Army scenes g01–g19
- Background: [`references/visual-fidelity-audit.md`](../../references/visual-fidelity-audit.md) covers what each upstream repository contains, its licence and its blockers.

## 1. What changed

The scenes were rebuilt on the upstream repositories' own renderers. Each renderer was first benchmarked against our adapter, and the gaps were fixed:

| Engine (upstream) | Native vs adapter, before fixes | After fixes | Evidence |
|---|---|---|---|
| huashu-art-motion (8 grammars, 33 frames) | 22.9–24.7 dB; 6 grammars crashed | **pixel-identical** (MAE 0.0) | `benchmarks/huashu_native_vs_adapter_{before,after}.jpg` |
| animate (4 styles, history-of-ai, Ghost Army piece) | 18.1 dB; wrong piece served from cache | **pixel-identical**, 24/24 frames | `benchmarks/animate_*` |
| lemo-opuscar (9 demos) | fonts missing → fallback face | within about 1.5 dB of the JPEG floor (33.7–47.2 dB) | `benchmarks/lemo_*`, `lemo_metrics.json` |
| mg-styles-15 (6 demos) | no viewport or motion blur | 30.6–70 dB (12 and 22 differ by WebGL raster noise only); motion blur 36.9–39.5 dB against a ~40 dB x264 ceiling | `benchmarks/mg_*` |
| dashi (4 templates) | — | black-gold identical; the others 17–25 dB **because Windows substitutes the macOS fonts they request** (the adapter itself is identical) | `benchmarks/dashi_*` |
| sweety-handdraw-video | — | native pipeline runs; vendored engine keeps part order and the nib-to-ink ≤ 9 px contract (tested) | `benchmarks/sweety_*` |

We do not claim pixel-perfect equivalence where it was not measured.

## 2. The 19 scenes

Narration, claims, chapters, order and timing are unchanged; the timeline is still 907.1 s. Only the visual layer was replaced.

| Scene | Before (rejected) | After: look and engine |
|---|---|---|
| g01 | blurred skyline | crosshatch night Rhine with German officers watching (animate) |
| g02 | flat beige map | night military map of the Viersen sector: Rhine, columns rolling in, two division symbols, observers, radio intercepts (mg-style d3/topojson) |
| g03 | words on black | crosshatch reveal: decoys outlined in red, "But those divisions were not there." (animate) |
| g04 | title card | handwritten title on a desk, unit stamp (animate) |
| g05 | stick figure + card | Ingersoll at a Fortitude planning map, typed memo (animate) |
| g06 | US map + text | cyanotype orders and route schematic (lemo blueprint) |
| g07 | counters + dots | kinetic type: 82 → 1,023 → ~1,100 → "Look and sound bigger" (huashu y5) |
| g08 | four icons | marker whiteboard org chart in narration order (lemo wb.js) |
| g09 | chart | editorial bar chart, approximate figures, dossier claim C7 order (huashu t3) |
| g10 | crowd dots | art school to U.S. Army studio (animate) |
| g11 | name cards | four hand-drawn portrait cards, labelled illustrative (animate) |
| g12 | four icons | whiteboard: four tools drawn stroke by stroke (lemo) |
| g13 | traced tank | an inflatable Sherman-like decoy inflated from a heap (animate) |
| g14 | stick figures | four soldiers lift the "tank", cyclists watch, ORAL HISTORY label (animate, morph from g13) |
| g15 | truck icon + list | half-track with a speaker array, drawn and painted (sweety_draw) |
| g16 | circles | "~15 miles", with an "estimate" caveat and a whiteboard aiming note (huashu y5 + y3) |
| g17 | network nodes | radio operator at his set, drawn and painted (sweety_draw) |
| g18 | icons + figure | patches painted, false markings stencilled, Bettembourg note (animate) |
| g19 | two lines | bulldozer making fake tracks, perimeter, men posing as MPs (animate, morph from g18) |

Before/after sheets sample the same timeline positions (30/60/90 % of each scene): `before-after/g01.jpg` … `g19.jpg` and `before-after/overview-1..4.jpg`.

## 3. Verification results

- **Tests:** `python -m unittest discover -s tests`: **109 tests OK** (67 before this branch).
  - New: `test_visual_qa`, `test_sweety_draw`, `test_html_seek_timing`, `test_animate_piece_timing`, `test_mg_map_page`.
  - Browser tests skip cleanly without Chromium.
- **Visual QA on g01–g19** (`visual_qa`, premium profile, scene files):
  - 0 blockers: no blank composition, no static scene, no fallback, no primitive engine.
  - Continuity is clean after the look-change dissolves.
  - Remaining warnings are `edge_clipping` on g05, g06, g09 and g19. Inspected by eye: g05 and g19 were textured desk or ground at the bottom edge, so false positives. A real bottom-edge clip of a caption card in g05/g19 was caught by this check and fixed.
- **`studio.py qa ghost-army --quality final`:**
  - 11/11 deliverables ok.
  - **Status: fail.** Its blockers are only the *legacy* scenes g30, g33, g35, g37, g39, g44 and g45 (blank compositions). These are outside the g01–g19 scope, still drawn by native engines, and flagged `allow_native` "pending". The same report lists 25 primitive-engine warnings for g20–g45. They are reported, not hidden.
- **Multilingual:** `studio.py dub ghost-army --lang es` gives `sample_pass`. The es track is 907.10 s against a 907.10 s master, with 0 issues, and the upload package was written.
- **Outputs** (local, under `projects/ghost-army/`, not in git):

| File | Size | Frame rate | Length | Audio |
|---|---|---|---|---|
| `renders/partial-g01-g19-final.mp4`: **preview of the rebuilt scenes** with narration, music and SFX | 1920×1080 | 30 fps | 374.9 s | yes |
| `renders/long-video.mp4`: the full documentary (g01–g19 rebuilt, g20–g45 legacy) | 1920×1080 | 30 fps | 907.1 s | yes |
| `shorts/short-ga1.mp4` | 1080×1920 | 30 fps | 26.9 s | yes |
| `shorts/short-ga2.mp4` | 1080×1920 | 30 fps | 31.8 s | yes |
| `shorts/short-ga3.mp4` | 1080×1920 | 30 fps | 26.8 s | yes |

  The Shorts are rebuilt with vertical huashu kinetic type and sweety; see `shorts-contact-sheet.jpg`.
- **Render cost** (final, 1080p, 4-core laptop, ms/frame):

| Engine | ms/frame |
|---|---|
| crosshatch (animate) | 409–726 |
| lemo / map (html_seek) | 264–349 |
| huashu | 150–261 |
| sweety_draw | 173–272 (plus a cached 35–70 s plan per illustration) |

  The full 45-scene build took 3042 s cold and 77 s when cached.

## 4. Known limitations

- **Figures.** Code-drawn characters, both the crosshatch paper-doll figures and the sweety tube-construction figures, read clearly and are period-correct, but they are not illustrator-grade portraits.
- **Camera moves.** In lemo whiteboard pans (g08, g12), labels are briefly cropped mid-move. In g18 the opening push crops the truck for about 3 s.
- **g16** ends on a sparse whiteboard note: a gear icon stands in for the weather station.
- **g02** has approximate positions and schematic roads, labelled in the corner.
- **dashi** templates are not used for Ghost Army; OFL aliases for their Mac fonts are not yet implemented.
- **whiteboard-animation-vi** is blocked (torch, cv2, scikit-image, gradio and model weights).
- **Legacy scenes.** The g20–g45 rebuild is the next step. Until then the long video mixes premium and legacy looks, and `studio.py qa` fails on the legacy scenes by design.

## 5. Build, test, rollback

```bash
python scripts/fetch_fonts.py --check
python -X utf8 -m unittest discover -s tests
python examples/ghost-army/build_project.py
python scripts/studio.py build ghost-army --quality final --only g01,g02,...,g19
python scripts/studio.py qa ghost-army --quality final
```

- **Fonts:** the `--check` flag restores or verifies the OFL fonts for lemo pages; run the script without it to fetch missing files.
- **Partial build:** the `--only g01,…,g19` build writes `renders/partial-g01-g19-final.mp4`.
- **Requirements:** Playwright Chromium, Node, and the external checkouts in `_upstream/` (huashu-art-motion, animate, lemo-opuscar, mg-styles-15-src, dashi-animationstyle). Paths can be overridden with `STUDIO_*_DIR`.
- **Rollback:** `main` is untouched (V1–V3). Check out `main`, or revert this branch's commits. Projects without `quality_profile` keep the V3 behaviour, including native fallbacks.
