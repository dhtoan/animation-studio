# AI voice engine (Edge-TTS + ElevenLabs MCP + SAPI)

## Modes (`project.voice.mode`, overridable per language in `voice.languages.<lang>.mode`)

| mode | what | cost | network | status on the dev machine |
|---|---|---|---|---|
| `edge-tts` | Microsoft neural voices via the `edge-tts` package | free | **yes**: text is sent to Microsoft's speech service | **verified 2026-10-14** (edge-tts 7.3.1, 322 voices, word boundaries) |
| `elevenlabs` | ElevenLabs via the **ElevenLabs MCP server connected to Claude Code** | uses account credits | yes | **not connected**: the adapter is ready but disabled until verified |
| `sapi` | Windows System.Speech voices | free | no (offline) | verified (David, Zira) |
| `auto` | ElevenLabs if verified **and** approved for the project, else edge-tts, else SAPI | — | — | — |
| `file` | your own recordings, `audio/voice/<scene>.wav` | — | no | — |

`auto` never picks ElevenLabs silently. It requires both of these:
1. `voice/provider-status.json` records a successful verification on this machine (git-ignored).
2. The project sets `"voice": {"elevenlabs": {"approved": true, "voice_id": "...", "model_id": "..."}}`.

## Edge-TTS settings
```json
"voice": {"mode": "edge-tts", "edge_rate": "-5%", "edge_pitch": "+0Hz",
          "languages": {"en-US": {"voice": "en-US-AndrewNeural"},
                        "es": {"voice": "es-MX-JorgeNeural"}, "de": {"voice": "de-DE-ConradNeural"},
                        "fr": {"voice": "fr-FR-HenriNeural"}, "ja": {"voice": "ja-JP-KeitaNeural"},
                        "pt-BR": {"voice": "pt-BR-AntonioNeural"}}}
```
- List voices with `python scripts/studio.py voice list --lang es`.
- Edge returns word boundaries, which drive cue timing, kinetic type and captions.

## ElevenLabs via MCP: verification workflow (run by Claude when the MCP server appears)
Python cannot call MCP tools. The provider is therefore **agent-delegated**:

1. **Discover.** List the tools the connected ElevenLabs MCP server actually exposes. Do not assume tool names.
2. **Authenticate and check allowances.** Call the server's account or subscription tool, if one exists, and record plan, character quota, used characters and reset date. Promotional terms the user reports (for example 12 months and 33 M characters) count as *reported* until the account data confirms them.
3. **Pick a voice and model** from the server's listings. Record `voice_id` and `model_id`.
4. **Sample.** Generate one short sentence and save it as `voice/elevenlabs-sample.mp3`. Then run `python scripts/studio.py voice verify-elevenlabs --sample voice/elevenlabs-sample.mp3 --plan "<plan>" --quota <chars> --used <chars> --voice-id <id> --model-id <id>`. This decodes and validates the audio and writes `voice/provider-status.json`.
5. **Enable per project.** Set `voice.elevenlabs.approved: true`.
6. **Produce:**
   - `python scripts/studio.py voice jobs <slug> --lang en-US` writes `audio/jobs/elevenlabs-<lang>.json`. Each entry has scene id, text, character count, target file and cache key, and **only uncached clips** are included.
   - Claude runs each job with the MCP text-to-speech tool and saves the file to the target path.
   - `python scripts/studio.py voice ingest <slug> --lang en-US` validates every file, converts it to WAV, aligns the words, and appends the character usage to `reports/voice-usage.json`.

No API keys are stored in this repository. The MCP server holds the credentials.

## Caching and usage
- Every clip is keyed by `sha256(provider, voice, rate, pitch, model, text)`. Unchanged text is never regenerated.
- `reports/voice-usage.json` appends a record per run (provider, requests, characters, cache hits) and keeps running totals per provider.
- For ElevenLabs, compare the totals with the quota recorded at verification. `voice jobs` refuses to emit jobs that would exceed the remaining recorded quota.
