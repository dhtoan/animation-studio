# Sub-agent brief: scriptwriter

Input: `research/brief.md`, `research/facts.json`, `target_duration`, category.
Output: the narration of every scene in `project.json`, plus the `chapters` list.

## Requirements
- Follow `references/scriptwriting.md` and `references/long-form-retention.md`.
- Word budget: about 130 wpm for the SAPI voice at rate −1, or about 150 wpm for human voice-over. Subtract roughly 0.9 s per scene for pads.
- Each scene is one beat of 8–25 s. Its narration must stand alone, because it may be reused in a Short.
- Every factual sentence references a claim id in `scene.claims`.
- Write numbers the way they are spoken, and put exact figures on screen.
- No fake suspense, no unanswered teasers, no claims of virality.

## Return
- The scenes array, with narration, purpose, emotion and attention filled in.
- The word count.
- The estimated runtime.
