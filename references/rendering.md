# Rendering

## Model
Every frame is a pure function of time: `frame = Engine(scene, t)`.
- Elements are rasterised on a supersampled canvas (2× at preview and final quality).
- An element is cached once its animation finishes, then composited into later frames.
- The camera crop, zoom and downscale happen in a single resize.
- A transition blends with the previous scene's last frame. That frame is re-rendered deterministically, so scenes can still render in parallel.

## Quality presets (fps is always 30)
| quality | long | short | ss | x264 |
|---|---|---|---|---|
| draft | 960×540 | 540×960 | 1 | crf 28, ultrafast |
| preview | 960×540 | 540×960 | 2 | crf 23, veryfast |
| final | 1920×1080 | 1080×1920 | 2 | crf 18, medium |

## Caching and resume
- Each scene renders to `<id>-<hash>.mp4` plus a JSON manifest.
- The hash covers:
  - the scene spec, timing and word times
  - render settings, theme, badge and captions
  - the engine code hash
  - the previous scene, when it blends with this one
- Unchanged scenes are skipped. If a build crashes, finished scenes stay intact, so re-running `build` resumes where it stopped.
- `--only s05,s06` renders just those scenes.
- A failed scene retries (`--retries`), then falls back along the router chain. Every attempt is logged in the manifest and in `reports/render-<quality>.json`.

## Measured cost (dev machine, 1080p, one core, ms/frame)
| engine | ms/frame |
|---|---|
| kinetic | 115 |
| motion | 115 |
| whiteboard | 120 |
| handdrawn | 135 |
| artistic | 145 (renders at 1×) |
| huashu_clip | ≈ 60 (Chromium) |
| animate_piece | ≈ 400 (Chromium) |

A 10-minute final with 4 workers takes about 15–20 minutes.

## External adapters
| engine | needs | configure |
|---|---|---|
| huashu_clip | huashu-art-motion checkout, Python `playwright`, a Chromium | `STUDIO_HUASHU_DIR`, `STUDIO_CHROMIUM` |
| animate_piece | cth9191/animate checkout, Node, `playwright`, a Chromium | `STUDIO_ANIMATE_DIR` |

- The same settings can be set under `external` in `studio.config.json`.
- Without them, `capabilities` reports `ok: false` and the router falls back to another engine.
- Upstream checkouts are never modified. animate pieces are copied into `scenes/_animate/` before `build.mjs` runs.

## Assembly
- Scene MP4s are concatenated with `-c copy`; this works because every scene uses identical encoder settings.
- The audio mix is normalised with `loudnorm I=-14 TP=-1.5` and muxed as AAC at 192k.
- Captions are a sidecar SRT for the long video, and are burned in for Shorts.
