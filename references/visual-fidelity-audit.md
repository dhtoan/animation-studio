# Visual-fidelity audit: upstream design implementations

This is the audit behind the `feature/visual-fidelity` upgrade. It covers each upstream repository, what it really contains, whether we may reuse it, how we drive it, and how close our integration comes to the repository's own renderer.

The audit was triggered by one finding: the Ghost Army scenes g01–g19 were rejected as "PowerPoint-like". The causes were:
- the studio's own Pillow engines, which drew stick figures, icon clip-art and flat maps;
- empty compositions;
- weak typography;
- silent fallbacks to those native engines.

## 1. Repositories, licences and status

**Benchmark.** "Native vs adapter" means the same page or spec is rendered two ways, at the same time t:
- with the repository's own tool;
- through our engine adapter.

The frames are then compared with PSNR and mean absolute difference (MAE). JPEG floor is the ceiling set by JPEG compression of the same frame.

| Repository | Licence | What we reuse | Integration | Native vs adapter benchmark | Status |
|---|---|---|---|---|---|
| alchaincyf/huashu-art-motion | MIT; fonts are OFL; likeness and mascot assets are excluded | The clip grammars `scripts/engine/clips/*.js`, the libraries `lib/*.js` and `clip.html` (`prepare`/`renderFrame`), plus `spec_assets.localize` | `engines/browser.py: HuashuClipEngine`, which drives the external checkout. Supports multi-shot scenes. | 8 grammars, 33 frames: **pixel-identical** (MAE 0.0). Before the fixes it was 22.9–24.7 dB, and 6 grammars crashed. | Integrated |
| cth9191/animate | MIT | The kit (`core.js`, `morph.js`, `styles/*/kit.js`), `build.mjs` and `index.html` `renderFrame` | `engines/browser.py: AnimatePieceEngine`, which builds a work copy. `params.timing` drives the eras. | 4 style demos, history-of-ai and the Ghost Army piece: **pixel-identical**, 24/24 frames. Before: 18.1 dB, and the wrong piece was cached. | Integrated |
| lemomo-ai/lemo-opuscar | MIT. Demo media follow CREDITS; fonts are OFL, fetched separately. | Style engines (whiteboard `wb.js`, blueprint `draw.js`/`paper.js`, …), `core/lib.js` and the `render(t)` contract | `engines/html_seek.py`, lemo contract: font manifest, `params.timing`/`era`, GPU, CDP JPEG capture, 3-page pool | 9 demos within about 1.5 dB of the JPEG floor (33.7–47.2 dB). Silent-film differs only in its scratch texture. | Integrated |
| Vincentwei1021/mg-styles-15 | MIT; a source-only clone | Demo pages (`window.DEMO`, `renderAt`), d3 + topojson maps, the SVG character rigs, harness motion blur | `engines/html_seek.py`, mg contract: `DEMO` viewport, sub-frame motion blur | 6 demos: 30.6–70 dB. The differences in 12 and 22 are WebGL rasterisation only. Motion blur: 36.9–39.5 dB against the x264 ceiling of about 40 dB. | Integrated (map for g02) |
| chuspeeism/dashi-animationstyle | MIT | Template base and scene layers, `timeline.js`, `动效部件.js`, the richness metric | `engines/html_seek.py`, dashi contract (staging) | 黑底科技 is identical. Other templates measure 17–25 dB **because Windows substitutes the macOS fonts they ask for**; the adapter is identical to Playwright loading the same page. | Integrated; fonts are a known gap |
| threerocks/sweety-handdraw-video | MIT | `stroke_paths`, `paint_motion`, `stroke_assets`, and the pen/lift logic from `video_renderer` | Vendored as `adapters/vendor/sweety_handdraw`; engine `sweety_draw` | Native pipeline runs (doctor/build/render/verify, exit 0). The vendored engine keeps the upstream part order and the nib-to-ink ≤ 9 px contract, both tested. | Integrated (vendored) |
| threerocks/sweety-image-art-direction | MIT | Art-direction rules, paraphrased | `references/image-art-direction.md` | — | Rules only |
| Kianzzz/xilo-opus-video | MIT | `render.py` harness (`window.render(t)`) and `audio_tools` SFX | Not wired. Its harness capability duplicates html_seek. | Ran a demo page natively: 4 s, 120 frames. `audio_tools` sfx check measured −19.7 LUFS. | Evaluated, not needed |
| letuandat131/whiteboard-animation-vi | CC0, MIT and Apache-2.0 | Grid planner, already vendored as `srt_whiteboard_grid` | `image_whiteboard` with `order: grid` | **Blocked.** The renderer needs torch/torchvision, cv2, scikit-image, safetensors and gradio, plus model weights from the network. None are installed or approved. | Blocked (dependencies) |
| Vincentwei1021/video-shotcraft | Apache-2.0 | Camera and transition parameters, shot grammar | `direction.py`, transitions (V2) | — | Integrated in V2 |
| cth9191/motion-design | **No licence** | Nothing; must not be copied | — | — | Excluded |
| WaterDJiang/Wattter_openSkills | **CC BY-NC-SA 4.0** (non-commercial) | Nothing; must not be copied | — | — | Excluded |

**The acceptance bar of at least 3 original implementations integrated, with their examples rendering, is met by 6:**
- huashu
- animate
- lemo
- mg
- dashi
- sweety

## 2. Source-to-component matrix

| Studio component | Upstream implementation it runs | Files in this repo |
|---|---|---|
| Look `historical-illustrated`: establishing shots, characters, recreations, morph bridges | animate crosshatch kit: `ink`, `paint`/`hatch`, `handwrite`, `pieceCam` push and bump, `BRIDGES` morphs, motion on 2s | `examples/ghost-army/pieces/crosshatch/` (scenes and figures authored for Ghost Army), `engines/browser.py` |
| Look `kinetic-type`: numbers, reveals, caveats | huashu `y5_kinetic_type`: spring slam, colour-band page wipes, progress rail | `engines/browser.py` (multi-shot), scene params in `build_project.py` |
| Look `data-editorial`: sourced charts | huashu `t3_finance_chart`: bars, highlight, source line, "Approximate" badge | as above |
| Look `premium-whiteboard`: org charts, the four tools | lemo whiteboard `wb.js`: marker stroke physics, pooled ink, floating pens, camera keys | `examples/ghost-army/pieces/lemo-whiteboard/` |
| Look `technical-blueprint`: orders and route schematic | lemo blueprint `draw.js`/`paper.js`: cyanotype shader, nib glow, `u`-progress primitives | `examples/ghost-army/pieces/lemo-blueprint/` |
| Look `military-map`: routes, unit symbols, observers | mg 22-hud: d3 `geoPath`, topojson land, graticule, HUD typography | `examples/ghost-army/pieces/mg-map/` |
| Look `hand-drawn-illustration`: equipment drawn stroke by stroke | sweety: part-ordered outline strokes, pen lifts, brush paint passes | `adapters/vendor/sweety_handdraw/`, `engines/sweety_draw.py`, `scripts/studio_lib/illustration/` (SVG kit, art for g13/g14/g15/g17) |
| Narration-timed eras across scenes | animate `ERA_LIST`/`TIMELINE`; lemo and mg page timing | `scripts/studio_lib/piece_timing.py`, engine `params.timing`/`era` |
| Typography | OFL families fetched from google/fonts, mapped by request path | `tools/fonts/manifest.json`, `scripts/fetch_fonts.py`, html_seek `resolve_font` |
| Quality-regression checks | dashi's richness metric (V2), plus the new checks | `scripts/studio_lib/visual_qa.py`, `qa.py` |
| No silent degradation | — (studio policy) | `engines/__init__.py` (TIER, `is_premium`), `router.py` (`EngineUnavailable`) |

## 3. Root causes of the rejected look, and the fix for each

1. **Primitive native drawings.** Fixed: every g01–g19 scene now uses an authentic engine. The `documentary-premium` profile forbids native engines unless a scene opts out with a stated reason.
2. **Silent fallbacks.** Fixed: in premium projects, fallbacks are restricted to authentic engines. The router raises `EngineUnavailable`, naming the missing dependency, and visual QA turns any fallback into a blocker.
3. **Adapter infidelity.** Fixed: the extra breathing camera, the forced theme, unresolved assets, wrong cache keys, missing fonts, the software rasteriser and lossy timing (24 vs 30 fps) were all corrected. Section 1 lists the measurements.
4. **Empty compositions and frozen holds.** These are now detected by `visual_qa` (blank composition, static scene). The authored pieces also hold a minimum and maximum beat time.
5. **Inconsistent typography and colour.** Addressed by the design system: shared palettes, semantic red (meaning fake or contested only), font roles, and a minimum text size of 28 px at 1080p.

## 4. Known gaps (not hidden)

- **dashi fonts.** The dashi templates request macOS fonts (PingFang, Songti, Hannotate). On Windows they render with substitutes, so output is not pixel-equivalent to the authors' Mac references. The proposed fix, OFL `@font-face` aliases, has not been implemented.
- **whiteboard-animation-vi** is blocked by heavy ML dependencies; see section 1.
- **Scenes g20–g45** of Ghost Army are outside the g01–g19 rebuild. They still use native engines and carry `allow_native` with the reason "pending".
- **Characters** in the crosshatch piece and in the sweety illustrations are code-drawn "paper doll" or tube-construction figures. They are recognisable and dressed for the period, but they are not illustrator-grade portraits.
- **No pixel-perfect claim** is made where none was measured: dashi on Windows, and mg WebGL demos (rasteriser noise).
