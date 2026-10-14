# youtube-multilingual-dubbing

The goal is one master video, one URL, and selectable audio languages. Do not upload duplicate videos per language.

## Workflow
1. **Master.** Render the English (US) long-form normally. Do not burn English captions into the master.
2. **Glossary** (`localization/glossary.json`). Lock names, units, ranks and dates:
   ```json
   {"terms": [{"term": "Ghost Army", "es": "Ejército Fantasma", "keep_note": "official translation used by…"},
              {"term": "Bill Blass", "keep": true}]}
   ```
3. **Translation** (`localization/<lang>/script.json`). Write natural narration per scene id; context-aware, not literal. Keep the meaning, names, dates and claims, and add the translated title and description:
   ```json
   {"lang": "es", "reviewed_by": "native reviewer name or 'pending'", "title": "…", "description": "…",
    "scenes": {"s01": "…", "s02": "…"}}
   ```
   Before publishing, a native speaker reviews the text and their name goes in `reviewed_by`. The QA report flags `pending`.
4. **Voice.** `studio.py dub <slug> --lang es` uses the voice engine: Edge-TTS by default, or ElevenLabs once verified and approved. Keep one consistent narrator identity per language. Never clone a voice without permission.
5. **Timing fit:**
   - Each dubbed scene must fit its master slot.
   - If it runs long, `atempo` speeds it up to at most **1.12×**.
   - If it is still too long, the scene is flagged so the translation can be shortened. It is never truncated and never overlaps the next scene.
6. **Mix.** The music and SFX bed is identical to the master. Loudness is normalised to −14 LUFS.
7. **Exports:**
   - `renders/audio-<lang>.wav` and `.m4a`, exactly the master duration (< 50 ms).
   - `subtitles/captions-<lang>.srt`.
   - `seo/localizations.json`.
   - `reports/dub-<lang>.json` (QA).
8. **Package.** `studio.py dub-package <slug>` writes `reports/multilingual-upload-package.md` with the YouTube Studio steps.

## Language priority
Enable languages from evidence, not by default:
- the channel's geography and traffic (Analytics)
- translation quality available
- production cost

Initial candidates are `es`, `de`, `fr`, `ja` and `pt-BR`. Spanish is usually the first test for a U.S. audience, but measure it.

## Upload
- There is no API endpoint for audio tracks, so upload in YouTube Studio. Steps are in the generated package and in `references/youtube-api-notes.md`.
- Check the channel has access to multi-language audio first.
