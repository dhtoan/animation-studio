"""youtube-multilingual-dubbing: one master video, one audio track per language.

Workflow (per language):
  English master timeline (storyboard/timeline.json)
  -> localization/glossary.json          locked names/terms per language
  -> localization/<lang>/script.json     translated narration per scene (written by the
                                         agent or a human translator; reviewed natively)
  -> voice engine (edge-tts by default; elevenlabs when verified + approved)
  -> per-scene fit into the master slot  (no overlap with the next scene; up to 1.12x
                                         tempo via ffmpeg atempo; longer = flagged for a
                                         shorter translation, never truncated)
  -> same music + SFX bed (M&E) as the master
  -> renders/audio-<lang>.wav + .m4a     exactly the master duration
  -> subtitles/captions-<lang>.srt, seo/localizations.json
  -> reports/dub-<lang>.json             QA: duration match, fits, glossary, peaks, chars

YouTube: the Data API has no endpoint for adding audio tracks (verified 2026-10-14,
see references/multilingual-dubbing.md); upload is manual in YouTube Studio.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

import numpy as np

from . import audio as A
from . import ffmpeg as FF
from . import subtitles
from .spec import load_project, save_json
from .tts import read_wav, write_wav

LANG_NAMES = {"es": "Spanish", "de": "German", "fr": "French", "ja": "Japanese", "pt-BR": "Portuguese (Brazil)",
              "en-US": "English (US)"}
MAX_TEMPO = 1.12        # quality limit for speeding up a dubbed line
HARD_TEMPO = 1.25       # emergency limit, used only to guarantee no overlap (always flagged)


def load_script(pdir: Path, lang: str) -> dict:
    f = pdir / "localization" / lang / "script.json"
    if not f.exists():
        raise FileNotFoundError(f"missing translation {f} (scene id -> translated narration)")
    return json.loads(f.read_text(encoding="utf-8"))


def glossary_check(src: dict[str, str], tr: dict[str, str], glossary: list[dict], lang: str,
                   partial: bool = False) -> list[str]:
    issues = []
    for sid, text in src.items():
        t = tr.get(sid, "")
        if not t.strip():
            if not partial:
                issues.append(f"{sid}: untranslated")
            continue
        for g in glossary:
            if g["term"].lower() in text.lower():
                want = g.get(lang) or (g["term"] if g.get("keep") else None)
                if want and want.lower() not in t.lower():
                    issues.append(f"{sid}: glossary term '{g['term']}' should appear as '{want}'")
        # digits must survive (dates written as numerals in either text)
        for num in re.findall(r"\b\d{2,4}\b", text):
            if num not in t:
                issues.append(f"{sid}: number {num} missing in translation")
    return issues


def _tempo(src: Path, dst: Path, factor: float) -> None:
    FF.run(["-y", "-i", str(src), "-filter:a", f"atempo={factor:.4f}", "-ar", "24000", "-ac", "1", str(dst)])


def dub(pdir: Path, lang: str, log=print) -> dict:
    from .tts import synthesize
    from .voice import log_usage, resolve

    p = load_project(pdir)
    tl = json.loads((pdir / "storyboard" / "timeline.json").read_text(encoding="utf-8"))
    loc = load_script(pdir, lang)
    gl_f = pdir / "localization" / "glossary.json"
    glossary = json.loads(gl_f.read_text(encoding="utf-8")).get("terms", []) if gl_f.exists() else []
    src = {s["id"]: s.get("narration", "") for s in p["scenes"] if s.get("narration")}
    tr = loc.get("scenes", {})
    partial = bool(loc.get("partial"))
    issues = glossary_check(src, tr, glossary, lang, partial)
    untranslated = [sid for sid in src if not tr.get(sid, "").strip()]
    cfg = resolve(p.get("voice", {}), lang)
    tts_cfg = {"provider": "edge" if cfg["mode"] == "edge-tts" else cfg["mode"], "mode": cfg["mode"], "voice": cfg["voice"],
               "edge_rate": cfg["rate"], "edge_pitch": cfg["pitch"], "allow_network": True,
               "rate": 0, "model": cfg.get("model")}
    if cfg["mode"] == "elevenlabs":
        raise RuntimeError("ElevenLabs dubbing runs through the agent-delegated MCP job flow (studio.py voice jobs)")
    cache = pdir / "audio" / "narration" / lang
    texts = {sid: t for sid, t in tr.items() if t.strip() and sid in src}
    narr = synthesize(texts, tts_cfg, cache, log=log)
    synthesized = [(k, texts[k]) for k, v in narr.items() if not v.get("cached")]
    log_usage(pdir, cfg, synthesized, cached=len(texts) - len(synthesized))
    rows = {r["id"]: r for r in tl["scenes"]}
    order = [r["id"] for r in tl["scenes"]]
    voice, fits, cues = [], [], []
    work = pdir / "audio" / "dub" / lang
    work.mkdir(parents=True, exist_ok=True)
    for i, sid in enumerate(order):
        if sid not in narr:
            continue
        r = rows[sid]
        start = r["start"] + r["lead"]
        slot_end = rows[order[i + 1]]["start"] if i + 1 < len(order) else tl["total"]
        avail = slot_end - start - 0.25
        d = narr[sid]["duration"]
        wav = Path(narr[sid]["wav"])
        factor = 1.0
        words = narr[sid]["words"]
        status = "fits"
        if d > avail:
            need = d / max(0.1, avail)
            factor = min(HARD_TEMPO, need)
            fitted = work / f"{sid}.wav"
            _tempo(wav, fitted, factor)
            wav = fitted
            words = [(t / factor, w) for t, w in words]
            d = d / factor
            status = "tempo" if factor <= MAX_TEMPO else "too_long"
            if factor > MAX_TEMPO:
                issues.append(f"{sid}: translation needs {need:.2f}x speed-up (quality limit {MAX_TEMPO}x) — shorten the translation")
            if d > avail + 0.02:  # even the emergency limit cannot fit: never overlap the next scene
                issues.append(f"{sid}: still {d - avail:.2f}s too long at {HARD_TEMPO}x — must be shortened before export")
        fits.append({"scene": sid, "slot": round(avail, 2), "voice": round(d, 2), "tempo": round(factor, 3), "status": status})
        voice.append((start, str(wav)))
        for c in subtitles.chunk(words, d + 0.3):
            st_, en_ = c["start"] + start, min(c["end"] + start, slot_end - 0.02)
            if en_ - st_ >= 0.3:  # drop cues that would collapse at the slot edge (already flagged above)
                cues.append({**c, "start": st_, "end": en_})
    # same M&E bed as the master
    from .pipeline import _music_plan, _sfx_events

    out_wav = pdir / "renders" / f"audio-{lang}.wav"
    info = A.mix(tl["total"], voice, _music_plan(p, tl), _sfx_events(p["scenes"], tl), out_wav,
                 p.get("music", {}).get("volume", 0.16), p.get("music", {}).get("enabled", True))
    norm = pdir / "renders" / f"audio-{lang}.norm.wav"
    FF.run(["-y", "-i", str(out_wav), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", str(norm)])
    shutil.move(str(norm), str(out_wav))
    m4a = pdir / "renders" / f"audio-{lang}.m4a"
    FF.run(["-y", "-i", str(out_wav), "-c:a", "aac", "-b:a", "192k", str(m4a)])
    subtitles.write_srt(cues, pdir / "subtitles" / f"captions-{lang}.srt")
    a, sr = read_wav(out_wav)
    dur = len(a) / sr
    pr = FF.probe(m4a)
    sub_issues = subtitles.check(subtitles.parse_srt(pdir / "subtitles" / f"captions-{lang}.srt"), tl["total"])
    rep = {"lang": lang, "language": LANG_NAMES.get(lang, lang), "provider": cfg["mode"], "voice": cfg["voice"],
           "provider_reason": cfg["reason"], "master_duration": tl["total"], "track_duration_wav": round(dur, 3),
           "track_duration_m4a": pr.duration, "duration_match": abs(dur - tl["total"]) < 0.05,
           "peak": round(float(np.max(np.abs(a))), 3), "scenes": len(fits),
           "fits": fits, "issues": issues + [f"subtitles: {x}" for x in sub_issues],
           "characters": sum(len(t) for t in texts.values()), "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "files": {"wav": str(out_wav), "m4a": str(m4a), "srt": str(pdir / "subtitles" / f"captions-{lang}.srt")}}
    rep["translation"] = {"scenes_translated": len(src) - len(untranslated), "scenes_total": len(src),
                          "untranslated": untranslated, "partial_sample": partial,
                          "native_review": loc.get("reviewed_by", "pending")}
    rep["status"] = "pass" if rep["duration_match"] and not rep["issues"] else "needs_attention"
    if partial and rep["status"] == "pass":
        rep["status"] = "sample_pass"  # technically valid track, but not a complete dub
    if loc.get("reviewed_by", "pending") == "pending":
        rep.setdefault("warnings", []).append("native-speaker review pending")
    save_json(pdir / "reports" / f"dub-{lang}.json", rep)
    # localized metadata
    lf = pdir / "seo" / "localizations.json"
    locs = json.loads(lf.read_text(encoding="utf-8")) if lf.exists() else {}
    if loc.get("title") or loc.get("description"):
        locs[lang] = {"title": loc.get("title", ""), "description": loc.get("description", "")}
        save_json(lf, locs)
    log(f"[dub] {lang}: {rep['status']} · {dur:.2f}s vs master {tl['total']:.2f}s · {len(fits)} scenes · "
        f"{sum(1 for f in fits if f['status'] == 'tempo')} tempo-fitted · {len(rep['issues'])} issues")
    return rep


def upload_package(pdir: Path, langs: list[str]) -> Path:
    p = load_project(pdir)
    L = [f"# Multilingual upload package — {p['title']}", "",
         "One master video, one YouTube URL, extra audio tracks + subtitles + localized metadata.", "",
         "## Files", "", "| Language | Audio track | Subtitles | Dub QA |", "|---|---|---|---|"]
    for lang in langs:
        r = pdir / "reports" / f"dub-{lang}.json"
        st = json.loads(r.read_text(encoding="utf-8"))["status"] if r.exists() else "not generated"
        L.append(f"| {LANG_NAMES.get(lang, lang)} (`{lang}`) | `renders/audio-{lang}.m4a` | `subtitles/captions-{lang}.srt` | {st} |")
    L += ["", "## YouTube Studio steps (verified against official help on 2026-10-14)", "",
          "1. Upload the **master** video (English narration) once.",
          "2. Multi-language audio requires access to the feature (Advanced features; may be limited to a subset of "
          "creators) — https://support.google.com/youtube/answer/13338784",
          "3. YouTube Studio (desktop) → **Languages** (named *Subtitles* in some help pages) → select the video → "
          "**Add language** → next to **Dub** click **Add** → select the `audio-<lang>` file → **Publish**. "
          "The track must be roughly the same length as the video (ours match to < 50 ms).",
          "4. If YouTube already created an *automatic dub* for that language, delete it before uploading yours "
          "(https://support.google.com/youtube/answer/15569972).",
          "5. Add `captions-<lang>.srt` under the same language → **Subtitles** → *Upload file* → *With timing* "
          "(https://support.google.com/youtube/answer/2734796).",
          "6. Add the translated title + description from `seo/localizations.json` (Studio → Languages → Title & "
          "description; via API this is `videos.localizations`).",
          "", "There is **no YouTube Data API endpoint to upload audio tracks** (verified in the v3 reference and "
          "revision history). This tool therefore never uploads; it prepares Studio-ready files.",
          "", "## Do not", "", "- Upload duplicate videos per language unless explicitly requested.",
          "- Burn English subtitles into the master (they would conflict with localized viewing).", ""]
    f = pdir / "reports" / "multilingual-upload-package.md"
    f.write_text("\n".join(L), encoding="utf-8")
    return f
