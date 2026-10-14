"""Animation Studio — production pipeline library.

Modules:
  config     formats, quality presets, paths
  ffmpeg     ffmpeg discovery, probing, encoding pipes
  spec       project/scene spec loading + validation
  design     design system (palettes, fonts, easing)
  draw       primitive drawing helpers (rough strokes, text, icons)
  engines/   animation engines (whiteboard, handdrawn, motion, kinetic, artistic, image_whiteboard)
  router     scene -> engine selection
  tts        narration providers (sapi, edge, file, silent-estimate)
  audio      procedural music/SFX + mixing
  timeline   narration-driven scene timing
  render     cached, resumable scene rendering
  assemble   concat + mux
  subtitles  SRT generation
  shorts     Shorts planning + rendering + mapping
  seo        YouTube metadata
  qa         quality checks + contact sheets
  research   fact ledger + rights checks
"""

VERSION = "0.1.0"
