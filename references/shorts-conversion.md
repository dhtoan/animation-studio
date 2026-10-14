# Shorts conversion (Shorts → long-form funnel)

## Selection
`studio.py shorts` writes `shorts/candidates.json`. It scores long-form scenes for standalone appeal using these signals:
- purpose is hook, reveal, data, metaphor or evidence
- concrete numbers
- questions
- emotion
- chart or stamp payoffs
- the author flag (`short_candidate`)

It then groups neighbouring scenes from the same chapter into 20–50 s windows. Pick 3–7 Shorts per video.

## Authoring a Short (`project.shorts[]`)
```json
{"id": "short-01", "title": "…", "chapter": "cracks", "duration_range": [15, 45], "publish_order": 1,
 "segments": [
   {"engine": "kinetic", "narration": "Immediate hook line.", "params": {"emphasis": ["…"]}},
   {"from": "s16", "narration": "Rewritten for a standalone idea.",
    "elements": [ "… with pos_v / box_v for vertical …" ]},
   {"from": "s17"}],
 "description": "…", "hashtags": ["#…"], "pinned_comment": "…"}
```
- **`from` scenes are re-rendered, never cropped.** The segment re-uses the long scene's engine, params and elements, rendered natively at 1080×1920.
- **Vertical layout:** override `elements` with vertical positions (`pos_v`, `box_v`). Without overrides, the vertical auto-layout stacks side-by-side items.
- **Narration and captions:** narration is re-synthesised, and captions are burned in, with the current word highlighted, inside the 9:16 safe zone.
- **CTA end card:** a CTA segment is appended automatically. Customise it with `cta` and `cta_label`, or disable it with `cta: ""`.

## Every Short must have
- An immediate hook in the first 1–2 s.
- One idea.
- Visible progression.
- A payoff.
- A natural pointer to the full video.

## Linking to the parent video
`shorts/shorts-map.json` records:
- the parent title and slug
- the chapter
- the source scenes and their timestamps
- a deep link, once `youtube_id` is set

In YouTube Studio, open each Short, go to **Details → Related video** and select the parent video. That is the supported clickable link from the Shorts player. This tool does not upload, so set the link manually.

No growth outcome is promised. Measure results in YouTube Analytics (Shorts → related-video clicks).
