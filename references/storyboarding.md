# Storyboarding

The storyboard **is** `project.json`; its schema is `schemas/project.schema.json`. `studio.py build` exports a timed, human-readable copy to `storyboard/storyboard.json` and `storyboard/storyboard.md`.

## Scene fields

| field | purpose |
|---|---|
| `id`, `chapter` | Stable id, used for caching and for mapping Shorts; chapters become YouTube chapters. |
| `narration` | The exact voice-over text. Timing is measured from TTS. |
| `purpose` | Drives the router. One of: hook, explain, process, data, comparison, timeline, story, character, metaphor, atmosphere, reveal, evidence, quote, recreation, tutorial, cta, illustration. |
| `attention`, `emotion` | What the viewer should notice or feel. Used by the router and in QA notes. |
| `visual` | A one-line description for humans. |
| `engine` | An explicit engine, or `auto`. |
| `shot`, `camera` | `shot` is `{type, angle}`. `camera` has `move` (drift \| push_in \| pull_out \| pan_left \| pan_right \| pan_up \| static), `amount`, `focus`, and `keys[{at, zoom, focus}]`. |
| `transition` | cut \| fade \| fade_black \| crossfade \| wipe \| erase \| push \| whip \| zoom_through \| slide_up, or `{type, dur}`. |
| `elements[]` | What moves (see below). |
| `audio.sfx[]` | `{name, at}`, where name is one of whoosh, thud, pop, tick, riser, impact, cash. |
| `assets[]` | `{path, license, source}`. Required for every external file. |
| `claims[]` | Ids in the facts ledger. |
| `illustrative` | Adds the badge to the scene when the project is fictional or illustrative. |
| `min_duration`, `pad` | Visual holds. |

## Elements (engine-agnostic)
Available types: `text`, `counter`, `icon`, `arrow`, `shape`, `stamp`, `card`, `image`, `bar_chart`, `line_chart`, `donut`, `network`, `timeline`, `process`, `list`, `character`, `crowd`, `particles`.

Common keys:
- `at`: when the element appears. Accepts seconds, `"40%"`, `"cue:word"`, `"cue:word#2"` or `"end-1.5"`.
- `dur`, `until`.
- `pos` / `box`: fractions of the 16:9 frame. Use `pos_v` / `box_v` for 9:16.

Icon names: building, factory, warehouse, truck, box, coin, dollar, bank, person, crowd, phone, laptop, server, chart_up, chart_down, warning, lock, document, magnifier, clock, rocket, house, globe, lightbulb, check, cross, arrow_right, handshake, star, flame, briefcase, gavel, cloud.

## Rules that prevent slideshows
- Every scene changes visibly at least every 3 s: something draws, grows, moves or counts.
- The camera always drifts unless it is set to `static`.
- Reveals are tied to narration cues, so the picture never runs ahead of the voice.
- No scene runs longer than about 30 s without a second visual event.
- QA runs `freezedetect` and flags 4 s with no pixel change.

## Contact sheets
- `studio.py preview <slug> --scene sNN` writes stills as PNGs.
- `studio.py qa` writes `previews/contact-sheet-*.png`, containing one mid-scene frame per scene plus the first frame of each transition.
