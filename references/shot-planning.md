# Shot planning and cinematic direction

Our own wording. The parameters and grammar are distilled from video-shotcraft's recipe cards and aesthetic rules (Apache-2.0) and from lemo-opuscar's DIRECTOR.md process (MIT). Attribution is in `THIRD_PARTY_NOTICES.md`.

## Process (per video)
1. **Treatment.** Write three one-paragraph structural options (for example chronological, cold-open-then-flashback, problem/solution). Pick one.
2. **Shot list.** One row per scene with: purpose, shot type, camera move, transition and the cue word that triggers the main action.
3. **Beat and cue map.**
   - Every element `at` is a `cue:word` taken from the narration.
   - The camera keys (`camera.keys`) land on emphasis words.
   - SFX (`audio.sfx`) land on impacts.
4. **Energy arc.** Each chapter rises toward its reveal and then breathes. Don't run three high-energy scenes back to back. A chapter opener re-hooks: it is not the lowest-energy scene of its chapter.
5. **Style frames.** Run `studio.py preview` on 1–2 key scenes per chapter before rendering everything.
6. **Self-check.** Use `references/quality-assurance.md`, the rubric, and `studio.py direction <slug>`.

## Shot vocabulary → engine camera

| shot | use | default camera |
|---|---|---|
| establishing | where we are (city, era, company) | `pull_out` |
| wide | systems, timelines, processes | `pan_right` / `drift` |
| medium | explanation, characters | `drift` |
| close | evidence, a number, a decision | `push_in` |
| insert | a single detail or word (hooks, stamps) | `push_in` |

`studio.py build` fills any missing `shot`, `camera` or `transition` from the scene `purpose`. Explicit values are never overwritten. The fills are logged in `reports/direction.json`.

## Camera parameters
- `push_in` / `pull_out` `amount`: 0.04–0.10. Keep slow pushes at roughly 1–1.5 % per second.
- `camera.keys`: `[{"at": "cue:collapsed", "zoom": 1.25, "focus": [0.7, 0.4], "dur": 0.6}]` gives a punch-in on a word.
- Don't add handheld shake by default. Shake is reserved for impacts (`crash_zoom` lands with a 14 px decaying shake).

## Transitions (budget: 1–2 "special" per chapter)

| transition | meaning |
|---|---|
| `cut` | default, continuity of thought |
| `crossfade` / `fade_black` | time passes / mood change / chapter break |
| `erase` | next idea on the same whiteboard |
| `push` / `whip` | energy, "meanwhile" |
| `zoom_through` | going deeper into a detail |
| `crash_zoom` | shock reveal: 6-frame 3.5 % pull-back → 6-frame ease-in push to 2.6× → landing shake |
| `flash_cut` | a hard fact lands (3 frames to white, 8 frames to the new shot) |
| `iris` | focus on one thing / circle match |
| `blinds` | list or step change |
| `glitch` | systems failing (use once) |
| `light_leak` | memory / nostalgia / dawn |

## House rules (`studio.py direction` checks them)
- No more than 3 full-frame impacts (stamps or slams) per video.
- No more than 3 consecutive scenes on the same engine; vary the look at chapter boundaries.
- No three identical shot types in a row.
- Text must be at least the `label` size (2.7 % of the short side) and readable on a phone.
- Hold any important text for at least 1 s after it finishes animating.
- Recurring characters keep the same colour role in every scene.
