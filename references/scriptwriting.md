# Scriptwriting (long-form)

## Structure (retention-first, no fake suspense)
1. **Cold open (0–30 s):** start on the most concrete moment of the story, such as a number, a contrast or a decision. No channel intro.
2. **Viewer promise (by ~45 s):** state what the viewer will understand by the end, and why it matters to them.
3. **Central question or conflict:** one sentence that the whole video answers.
4. **Developments:** 3–5 chapters. Each one opens with a new question and ends with a partial answer that raises the next question (a curiosity bridge). Never tease something you won't deliver.
5. **Evidence:** every claim needs something to show (a chart, a document or a process diagram) and an entry in the ledger.
6. **Answer:** resolve the central question explicitly.
7. **Takeaway:** give the viewer a tool, such as a checklist, a question to ask or a model, then bridge to the next video.

## Language
- Write in American English, in a spoken register: short sentences, concrete nouns, active verbs.
- Write numbers the way the narrator says them ("one point four billion dollars"). Put the precise figure on screen.
- Keep one idea per sentence. Don't stack three clauses in a sentence meant for TTS.
- Make each scene's narration stand alone, because scenes are re-used by Shorts.

## Length budgeting

| runtime | words at ≈130 wpm (SAPI rate −1, measured) | words at ≈150 wpm (human) |
|---|---|---|
| 10 min | ≈ 1,250 | ≈ 1,450 |
| 15 min | ≈ 1,900 | ≈ 2,200 |
| 20 min | ≈ 2,500 | ≈ 2,900 |
| 25 min | ≈ 3,100 | ≈ 3,600 |

- Each scene adds lead and tail pads of about 0.9 s.
- `build` measures the timeline from real TTS and reports the deviation from `target_duration`. It must stay within `tolerance` (default ±5 %).
- Fix the length by editing the narration, not by stretching holds. `--fit` exists for small gaps only.

## Scene sizing
- Aim for 8–25 s per scene: one beat and one visual idea.
- Split anything over ~30 s into two scenes, with a different engine or camera move.
