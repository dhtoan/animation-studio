# Animation Studio

A Claude Code skill and Python pipeline. It takes a researched topic through to a finished, QA-checked animated YouTube video and its Shorts. Everything renders locally from code, with no paid generation APIs.

```
Topic → Research (claims ledger) → Script → Storyboard (project.json) → Art direction → Engine routing
→ Narration (word timings) → Scene rendering (cached, parallel) → Music/SFX mix → Captions
→ 16:9 assembly → 9:16 Shorts (recomposed, captioned, linked to parent) → SEO package → QA report
```

## What it produces
`projects/<slug>/` contains:

| Folder | Contents |
|---|---|
| `research/` | `brief.md`, `facts.json` |
| `scripts/` | `narration.txt` |
| `storyboard/` | `storyboard.json`, `storyboard.md`, `timeline.json` |
| `scenes/` | Cached per-scene MP4s and manifests |
| `audio/` | Narration clips, `mix.wav` |
| `subtitles/` | `captions.srt` |
| `renders/` | `long-video.mp4` |
| `shorts/` | `short-01.mp4` …, `shorts-map.json`, `candidates.json` |
| `seo/` | `youtube-metadata.md` / `.json`, `shorts-metadata.md` |
| `thumbnails/` | `thumbnail.png` |
| `previews/` | Contact sheets |
| `reports/` | `quality-report.json`, `asset-license-report.md`, render reports, build log |

## Install
```bash
pip install -r requirements.txt
```
- **ffmpeg**: any ffmpeg on PATH works. Alternatively, `imageio-ffmpeg` (in requirements) ships one, or set `STUDIO_FFMPEG`.
- **Use as a Claude Code skill**: clone this repository as a skill folder:
  ```bash
  git clone https://github.com/dhtoan/animation-studio.git ~/.claude/skills/animation-studio
  ```
  (or into a project's `.claude/skills/animation-studio`). `SKILL.md` is at the repository root.
- **Optional adapters**:
  - `pip install playwright`, plus any Chromium (Playwright's own, or set `STUDIO_CHROMIUM`).
  - A checkout of [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) (`STUDIO_HUASHU_DIR`).
  - A checkout of [cth9191/animate](https://github.com/cth9191/animate) with Node (`STUDIO_ANIMATE_DIR`).
  - You can also put these paths in `studio.config.json`; see `studio.config.example.json`.

Check what's available:
```bash
python scripts/studio.py capabilities
```

## Quick start
```bash
python scripts/studio.py init my-video --category business --duration 600 --title "My Video"
# edit projects/my-video/project.json (see examples/billion-dollar-collapse) + research/facts.json
python scripts/studio.py validate my-video
python scripts/studio.py dry-run my-video
python scripts/studio.py preview my-video --scene s01
python scripts/studio.py build my-video --quality draft
python scripts/studio.py build my-video --quality final --workers 4
python scripts/studio.py shorts my-video --quality final
python scripts/studio.py seo my-video --quality final
python scripts/studio.py qa my-video --quality final
python scripts/studio.py review my-video --approve --notes "checked contact sheets"
```

## Demo
`examples/billion-dollar-collapse/` is "The Billion-Dollar Business That Collapsed Overnight". It features a **fictional** company, runs 34 scenes, about 10 minutes, and uses 7 engines and 3 Shorts.
```bash
python examples/billion-dollar-collapse/build_project.py          # regenerate project.json
mkdir -p projects/billion-dollar-collapse/research
cp examples/billion-dollar-collapse/project.json projects/billion-dollar-collapse/
cp examples/billion-dollar-collapse/research/facts.json projects/billion-dollar-collapse/research/
python examples/billion-dollar-collapse/make_assets.py projects/billion-dollar-collapse
python scripts/studio.py build billion-dollar-collapse --quality final --workers 4
```

## Engines
- **Native** (always available):
  - `whiteboard`
  - `handdrawn`
  - `motion`
  - `kinetic`
  - `artistic`
  - `image_whiteboard` (uses vendored upstream stroke and grid planners)
- **Adapters** (external checkouts):
  - `huashu_clip`
  - `animate_piece`

See [references/rendering.md](references/rendering.md) and [references/source-audit.md](references/source-audit.md).

## V2: styles, art direction, shot planning
```bash
python scripts/studio.py styles                 # registry with verified status
python scripts/studio.py styles --verify        # render a 3 s sample per style on this machine
python scripts/studio.py direction my-video     # style bible, shot plan, continuity, style proposal
```
- Scenes can set `art_style` (a registry id) instead of an engine.
- Missing `shot`, `camera` and `transition` values are planned automatically from the scene `purpose` and chapter structure.
- New cinematic transitions: `crash_zoom`, `flash_cut`, `iris`, `blinds`, `glitch`, `light_leak`.
- The `html_seek` engine drives lemo-opuscar, dashi-animationstyle, or your own seekable HTML pages:
  - Set `STUDIO_LEMO_DIR` and `STUDIO_DASHI_DIR` for those checkouts.
  - Upstream pages stay unmodified, and every network request outside 127.0.0.1 is blocked.
- `reports/production-report.json` records stage timings, cache hits, worker render seconds, engines used, and paid services used (none).
- `examples/v2-style-showcase/` is a ~45 s demo that mixes 5 verified styles and includes a vertical Short.

## V3: documentary intelligence, research, dubbing, analytics
```bash
python scripts/studio.py niche score --dir examples/niche-research        # rank 20 cited ideas + 30-episode roadmap
python scripts/studio.py history ghost-army import --dossier examples/ghost-army/research/dossier.json
python scripts/studio.py history ghost-army report                         # fact-check report before rendering
python scripts/studio.py story plan --minutes 18                           # section budgets
python scripts/studio.py story check ghost-army
python scripts/studio.py audience ghost-army                               # 50+ presentation audit (pace, contrast, text)
python scripts/studio.py dub ghost-army --lang es                          # audio-es.wav/.m4a + captions-es.srt + QA
python scripts/studio.py analytics --exports analytics/exports             # Studio CSV exports -> progress + recommendations
```
- **Niche research works without paid services.**
  - Evidence comes from public pages (with URL and date), from the Data API (`YT_API_KEY`, opt-in, quota-budgeted), or from CSV.
  - Scores are transparent and weight-configurable. Missing evidence lowers confidence.
  - RPM is never estimated for other channels.
- **Historical research:**
  - Source tiers: National Archives, Library of Congress, Smithsonian, museums, then academic, then press.
  - Claims are classed as established, contested, allegation or reconstruction, and contested claims are framed on screen.
- **New visual tools:** a `map` element (GeoJSON, e.g. public-domain Natural Earth) and an `archival` engine for labelled recreations.
- **Accessibility:** text colours are auto-corrected to WCAG AA contrast against each engine's background.
- **Multilingual output:**
  - One master video; per-language audio fitted into each scene slot with no overlap.
  - The master's music and SFX bed is reused.
  - Exports: exact-length WAV/AAC, localized SRT and metadata, plus Studio upload steps.
  - The YouTube API cannot upload audio tracks, so upload is manual.

## Voice engine (Edge-TTS + ElevenLabs MCP)
```bash
pip install edge-tts                                   # free; needs internet (Microsoft's speech service)
python scripts/studio.py voice status
python scripts/studio.py voice list --lang es
python scripts/studio.py voice sample --lang en-US     # writes + validates voice/samples/sample-edge-tts-en-US.wav
```
Project config:
```json
"voice": {"mode": "auto", "edge_rate": "-10%",
          "languages": {"es": {"voice": "es-MX-JorgeNeural", "rate": "+4%"}},
          "elevenlabs": {"approved": false, "voice_id": "", "model_id": ""}}
```
- **Modes:** `auto` picks ElevenLabs only when it is verified *and* approved; otherwise it uses `edge-tts`, then `sapi`. You can also set the mode explicitly.
- **Caching:** clips are cached by `sha256(provider, voice, rate, pitch, model, text)`.
- **Usage tracking:** usage is appended to `reports/voice-usage.json`.
- **ElevenLabs** works through its MCP server once that server is connected to Claude Code. See `references/voice-engine.md` for discovery, verification, jobs, ingest and the quota guard.
  - No API keys are stored in this repository.
  - It stays disabled until `voice verify-elevenlabs` records a successful sample.

## Narration
| Provider | Notes |
|---|---|
| `sapi` | Local Windows voices, with word timings aligned to the audio's pauses |
| `edge` / `edge-tts` | Free online neural voices (Microsoft). Opt in with `voice.mode: "edge-tts"` or `voice.allow_network: true` |
| `file` | Your own recordings |
| `estimate` | Silent placeholder; QA blocks it from delivery |

On non-Windows systems, use `edge` (opt-in) or `file`.

## Tests
```bash
python -m unittest discover -s tests -v
```

## Configuration
| Setting | Purpose |
|---|---|
| `STUDIO_PROJECTS_DIR` | Projects root (default `./projects`) |
| `STUDIO_FFMPEG` | ffmpeg path |
| `STUDIO_CHROMIUM` | Chromium path |
| `STUDIO_HUASHU_DIR` | huashu-art-motion checkout |
| `STUDIO_ANIMATE_DIR` | cth9191/animate checkout |
| `STUDIO_LEMO_DIR`, `STUDIO_DASHI_DIR`, `STUDIO_MG_DIR` | html_seek upstream checkouts |
| `YT_API_KEY` | optional Data API key for live niche collection |
| `YT_ANALYTICS_TOKEN` | optional OAuth access token for owned-channel analytics (read-only) |
| `STUDIO_FONT_DIR` | Extra fonts |

For licensed, distributable typography, drop OFL fonts into `assets/fonts/`.

## Limits (honest)
- The default voice is a Windows system voice. Publication quality needs licensed voice talent or a neural TTS you are allowed to use.
- Characters are simple procedural figures. Richer art needs licensed illustrations, fed through `image_whiteboard` or `image` elements.
- No uploading or publishing happens. Related-video links for Shorts are set manually in YouTube Studio.
- Nothing here predicts or guarantees views or growth.

## Licence and attribution
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
