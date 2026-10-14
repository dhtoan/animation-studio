# Quality assurance (`studio.py qa`)

## Automated checks
Results go to `reports/quality-report.json`.

| check | how |
|---|---|
| Resolution, aspect ratio, fps | Probe compared against the format and quality preset |
| Duration and constant frame rate | Container duration vs. timeline (±0.15 s); decoded frame count vs. duration × 30 (±2 frames) |
| Audio present, levels | Stream probe; RMS and peak of the mix |
| Black frames | `blackdetect d=0.5`, ignoring the opening fade |
| Frozen scenes | `freezedetect n=0.0008 d=4` (reported as a warning) |
| Unexpected silence | Gaps over 4 s between narration clips |
| Subtitles | Cues are in order, don't overlap, end within the video, fit in ≤ 2 lines of 42 characters, and have a sane reading speed |
| Missing assets, licences | Spec compared with files on disk; licence report |
| Research and rights | Claims-ledger gate; unresolved rights |
| Narration deliverable | The `estimate` provider is a placeholder, so it is a blocker |
| Shorts | 9:16 resolution; duration within `duration_range` |

## Visual review (required, by a human or an agent)
QA exports these contact sheets:
- `previews/contact-sheet-long-<q>.png`: mid-scene and transition-in frames
- one sheet per Short

Open them and check:
- Text is readable at phone size, with no clipping or overlaps.
- The pen lines up with the elements it draws.
- Colour meaning stays consistent.
- Illustrative scenes carry their badges.
- Transitions look intentional.
- Captions stay inside the safe zone.

Record the result:
- `studio.py review <slug> --approve --notes "…"` to approve.
- The same command without `--approve` to request changes.

Until the review is recorded, QA reports `pass_with_warnings` at best.

## Self-critique rubric
Score each item 1–10. Any item below 8 gets one more iteration. This rubric is adapted from the xilo-opus-video workflow (MIT); the wording is our own.
1. **Clarity**: one idea per scene.
2. **Sync**: visuals land on the spoken words.
3. **Readability**: legible on a phone.
4. **Motion purpose**: motion explains, it doesn't decorate.
5. **Consistency**: palette, type and characters stay the same throughout.
6. **Accuracy**: the ledger matches the screen.
7. **Polish**: transitions, audio levels, no glitches.

## When a deliverable counts as done
All three must be true:
- The file exists.
- Its automated checks report no issues.
- The visual review is approved.
