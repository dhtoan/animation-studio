# Copyright, licensing and risk

## Assets
- **Licence records are required.** Every external file a scene uses needs `assets: [{path, license, source}]`. `validate` reports an error when the licence is missing, and QA writes `reports/asset-license-report.md`.
- **Studio-generated material** (frames, music, SFX, procedural illustrations) is the original work of the project owner.
- **Narration via Windows SAPI** is generated locally. Check Microsoft's terms before commercial publication, or use licensed voice talent.
- **Fonts** are system fonts resolved locally. For output that is safe to distribute, add OFL fonts to `assets/fonts/`.
- **Never use** third-party characters, logos, footage, music or "finished scenes" from other creators.
- **Upstream demo media is excluded from reuse**: the huashu likeness and mascot assets, the whiteboard-animation-vi hand PNGs, and the sweety hosted hand sprites.
- **Unresolved rights** go into `project.rights_issues`. Any entry whose `status` is not `"resolved"` blocks QA.

## Upstream code (see `THIRD_PARTY_NOTICES.md`)
| component | licence | how used |
|---|---|---|
| `adapters/vendor/srt_whiteboard_grid/grid_stream.py` | MIT (SRT Whiteboard, via whiteboard-animation-vi) | vendored, notice kept |
| `adapters/vendor/sweety_stroke_paths/stroke_paths.py` | MIT (threerocks) | vendored, notice kept |
| huashu-art-motion | MIT | external checkout, driven by an adapter |
| cth9191/animate | MIT | external checkout, driven by an adapter |
| cth9191/motion-design | **no licence** | not used; linked only |

## Reputational risk
These rules apply to business, money, scandal and mystery topics.
- **Allegations** need sources and attribution ("prosecutors alleged…").
- **Outcomes** need court or regulator records.
- **No wrongdoing by association**: never place an image of a real person next to the word "fraud", or similar.
- **Claims about named living people or active companies** must be marked `risk: "high"`, and so must be `verified`.
- **When the goal is teaching a mechanism**, prefer a fictional composite.
