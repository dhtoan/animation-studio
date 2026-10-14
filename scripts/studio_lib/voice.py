"""Unified AI voice engine: provider selection, caching, character accounting.

Modes (project.voice.mode or per-language override):
  edge-tts     free Microsoft neural voices via `edge-tts` (online service, no key)
  elevenlabs   premium; runs through the ElevenLabs **MCP server connected to Claude Code**.
               Python cannot call MCP tools itself, so this provider is *agent-delegated*:
               `studio.py voice jobs` writes a job manifest, Claude executes it with the
               MCP tools it discovers, `studio.py voice ingest` validates + imports the audio.
  sapi         local Windows voices (offline drafts)
  auto         elevenlabs if verified + approved for this project, else edge-tts, else sapi

Safety rules implemented here:
  * ElevenLabs is never selected unless `voice/provider-status.json` records a successful
    verification AND the project sets `voice.elevenlabs.approved: true` (no silent spend).
  * Every synthesis request is keyed by sha256(provider, voice, settings, text); identical
    requests are never regenerated; usage is appended to reports/voice-usage.json.
  * No API keys are read or written by this module.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .config import SKILL_ROOT

STATUS_FILE = SKILL_ROOT / "voice" / "provider-status.json"  # machine-local, git-ignored
DEFAULT_VOICES = {
    "edge-tts": {"en-US": "en-US-AndrewNeural", "es": "es-MX-JorgeNeural", "de": "de-DE-ConradNeural",
                 "fr": "fr-FR-HenriNeural", "ja": "ja-JP-KeitaNeural", "pt-BR": "pt-BR-AntonioNeural"},
    "sapi": {"en-US": "Microsoft David Desktop"},
}


def provider_status() -> dict:
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {}


def save_status(st: dict) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def elevenlabs_ready(project_voice: dict) -> tuple[bool, str]:
    st = provider_status().get("elevenlabs", {})
    if not st.get("verified"):
        return False, "ElevenLabs MCP not verified on this machine (run the verification workflow)"
    if not (project_voice.get("elevenlabs") or {}).get("approved"):
        return False, "project has not approved ElevenLabs usage (voice.elevenlabs.approved)"
    return True, "verified + approved"


def edge_ready() -> tuple[bool, str]:
    try:
        import edge_tts  # noqa: F401
    except Exception:
        return False, "pip install edge-tts"
    return True, "installed (requires internet access to Microsoft's speech service)"


def resolve(project_voice: dict, lang: str = "en-US") -> dict:
    """Pick the provider + voice for a language. Returns the effective config."""
    per = (project_voice.get("languages") or {}).get(lang, {})
    mode = per.get("mode") or project_voice.get("mode") or project_voice.get("provider") or "auto"
    reason = "explicit"
    if mode == "auto":
        ok, why = elevenlabs_ready(project_voice)
        if ok:
            mode, reason = "elevenlabs", why
        elif edge_ready()[0]:
            mode, reason = "edge-tts", f"auto: {why}; using free edge-tts"
        else:
            mode, reason = "sapi", "auto: no online provider; local SAPI"
    if mode == "elevenlabs":
        ok, why = elevenlabs_ready(project_voice)
        if not ok:
            raise RuntimeError(f"ElevenLabs selected but not usable: {why}")
    voice = per.get("voice") or (project_voice.get("voice") if lang == project_voice.get("lang", "en-US") else None)
    if mode in DEFAULT_VOICES and (not voice or (mode == "edge-tts" and "Neural" not in str(voice))):
        voice = DEFAULT_VOICES[mode].get(lang) or DEFAULT_VOICES[mode].get(lang.split("-")[0])
    if mode == "elevenlabs":
        voice = per.get("voice_id") or (project_voice.get("elevenlabs") or {}).get("voice_id")
    return {"mode": mode, "voice": voice, "lang": lang, "reason": reason,
            "rate": per.get("rate", project_voice.get("edge_rate", "-5%")),
            "pitch": per.get("pitch", project_voice.get("edge_pitch", "+0Hz")),
            "model": per.get("model") or (project_voice.get("elevenlabs") or {}).get("model_id")}


def request_key(cfg: dict, text: str) -> str:
    return hashlib.sha256(json.dumps([cfg["mode"], cfg.get("voice"), cfg.get("rate"), cfg.get("pitch"),
                                      cfg.get("model"), text], ensure_ascii=False).encode()).hexdigest()[:16]


def log_usage(pdir: Path, cfg: dict, items: list[tuple[str, str]], cached: int) -> dict:
    """items: [(key, text)] actually synthesized. Appends to reports/voice-usage.json."""
    f = pdir / "reports" / "voice-usage.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"runs": [], "totals": {}}
    chars = sum(len(t) for _, t in items)
    run = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "provider": cfg["mode"], "voice": cfg.get("voice"),
           "lang": cfg.get("lang"), "requests": len(items), "characters": chars, "cache_hits": cached}
    data["runs"].append(run)
    tot = data["totals"].setdefault(cfg["mode"], {"characters": 0, "requests": 0})
    tot["characters"] += chars
    tot["requests"] += len(items)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return run


# ------------------------------------------------------------------ edge voices
def list_edge_voices(lang: str | None = None) -> list[dict]:
    import asyncio

    import edge_tts

    vs = asyncio.run(edge_tts.list_voices())
    if lang:
        vs = [v for v in vs if v["Locale"].lower().startswith(lang.lower())]
    return [{"name": v["ShortName"], "locale": v["Locale"], "gender": v.get("Gender")} for v in vs]


# ------------------------------------------------------------------ ElevenLabs (agent-delegated via MCP)
def verify_elevenlabs(sample: Path, plan: str | None, quota: int | None, used: int | None,
                      voice_id: str | None, model_id: str | None, tools: list[str] | None = None) -> dict:
    """Record a successful MCP verification after Claude generated `sample` with the MCP server."""
    from . import ffmpeg as FF

    if not sample.exists():
        raise FileNotFoundError(f"sample not found: {sample}")
    pr = FF.probe(sample)
    if not pr.has_audio or pr.duration < 0.5:
        raise RuntimeError(f"sample is not valid audio (duration {pr.duration}s)")
    st = provider_status()
    st["elevenlabs"] = {"verified": True, "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "via": "mcp",
                        "sample": str(sample), "sample_duration": pr.duration, "plan": plan,
                        "quota_characters": quota, "used_characters_at_verification": used,
                        "voice_id": voice_id, "model_id": model_id, "mcp_tools_seen": tools or []}
    save_status(st)
    return st["elevenlabs"]


def elevenlabs_jobs(pdir: Path, texts: dict[str, str], cfg: dict, lang: str) -> Path:
    st = provider_status().get("elevenlabs", {})
    cache = pdir / "audio" / "narration" / f"elevenlabs-{lang}"
    jobs, chars = [], 0
    for sid, text in texts.items():
        k = request_key(cfg, text)
        target = cache / f"{k}.mp3"
        if (cache / f"{k}.wav").exists():
            continue
        jobs.append({"scene": sid, "text": text, "characters": len(text), "voice_id": cfg.get("voice"),
                     "model_id": cfg.get("model"), "target": str(target), "key": k})
        chars += len(text)
    usage = json.loads((pdir / "reports" / "voice-usage.json").read_text(encoding="utf-8")) \
        if (pdir / "reports" / "voice-usage.json").exists() else {"totals": {}}
    spent = usage.get("totals", {}).get("elevenlabs", {}).get("characters", 0)
    quota, used0 = st.get("quota_characters"), st.get("used_characters_at_verification") or 0
    if quota is not None and used0 + spent + chars > quota:
        raise RuntimeError(f"ElevenLabs jobs need {chars} chars but only {quota - used0 - spent} remain of the recorded quota")
    out = pdir / "audio" / "jobs" / f"elevenlabs-{lang}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"provider": "elevenlabs", "lang": lang, "characters": chars, "jobs": jobs,
                               "instructions": "Claude: for each job call the connected ElevenLabs MCP text-to-speech tool "
                                               "with text/voice_id/model_id and save the audio to `target`; then run "
                                               "`studio.py voice ingest`."}, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def elevenlabs_ingest(pdir: Path, lang: str) -> dict:
    from . import ffmpeg as FF
    from .tts import align_words, estimate_words, wav_duration

    jf = pdir / "audio" / "jobs" / f"elevenlabs-{lang}.json"
    data = json.loads(jf.read_text(encoding="utf-8"))
    done, missing = [], []
    for j in data["jobs"]:
        src = Path(j["target"])
        if not src.exists():
            missing.append(j["scene"])
            continue
        wav = src.with_suffix(".wav")
        FF.run(["-y", "-i", str(src), "-ac", "1", "-ar", "24000", str(wav)])
        d = wav_duration(wav)
        words, info = align_words(estimate_words(j["text"], d), wav)
        src.with_suffix(".words.json").write_text(json.dumps({"provider": "elevenlabs", "words": words, "alignment": info}),
                                                  encoding="utf-8")
        done.append((j["key"], j["text"]))
    cfg = {"mode": "elevenlabs", "voice": data["jobs"][0]["voice_id"] if data["jobs"] else None, "lang": lang}
    run = log_usage(pdir, cfg, done, cached=0)
    return {"ingested": len(done), "missing": missing, "usage": run}


def sample(lang: str, text: str, out_dir: Path, cfg_voice: dict | None = None) -> dict:
    """Synthesize + validate a short sample with the provider `resolve` picks for `lang`."""
    import numpy as np

    from . import ffmpeg as FF
    from .tts import read_wav, synthesize

    cfg = resolve(cfg_voice or {"mode": "edge-tts"}, lang)
    if cfg["mode"] == "elevenlabs":
        raise RuntimeError("ElevenLabs samples are produced through MCP (see references/voice-engine.md)")
    tts_cfg = {"provider": "edge" if cfg["mode"] == "edge-tts" else cfg["mode"], "mode": cfg["mode"], "voice": cfg["voice"],
               "edge_rate": cfg["rate"], "edge_pitch": cfg["pitch"], "allow_network": True}
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = synthesize({"sample": text}, tts_cfg, out_dir, log=lambda *a: None)["sample"]
    wav = Path(rec["wav"])
    a, sr = read_wav(wav)
    pr = FF.probe(wav)
    rms = float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0
    ok = pr.duration > 0.5 and rms > 0.005 and len(rec["words"]) >= max(1, len(text.split()) // 2)
    named = out_dir / f"sample-{cfg['mode']}-{lang}.wav"
    import shutil

    shutil.copy2(wav, named)
    return {"ok": ok, "lang": lang, "provider": cfg["mode"], "voice": cfg["voice"], "file": str(named),
            "duration": round(pr.duration, 2), "sample_rate": sr, "rms": round(rms, 4),
            "word_boundaries": len(rec["words"]), "words_in_text": len(text.split()), "characters": len(text)}
